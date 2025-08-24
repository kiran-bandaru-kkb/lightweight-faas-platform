AryaXAI Lightweight FaaS Platform: Design Document
1. High-Level Architecture
The AryaXAI FaaS platform is designed for maximum performance and control in an internal setting. It follows a classic disaggregated architecture, separating the control plane from the data plane.

Architectural Diagram
text
+----------------+      +---------------------+      +-------------------------+
|                |      |                     |      |                         |
|   API Gateway  |----->|    Orchestrator     |----->|      Worker Pool        |
|   (Django)     |<-----|   (Django Core)     |<-----|   (Runtime Hosts)       |
|                |      |                     |      |                         |
+----------------+      +---------------------+      +------------+------------+
                                                                  |
                                                                  |
                                                    +-------------+-------------+
                                                    |                           |
                                                    |   Function Instance A     |
                                                    |   (runtime_host.py)       |
                                                    |                           |
                                                    +---------------------------+
                                                    |                           |
                                                    |   Function Instance B     |
                                                    |   (runtime_host.py)       |
                                                    |                           |
                                                    +---------------------------+
Component Descriptions
API Gateway: A Django application serving as the public entry point. It handles authentication, rate limiting, and routes incoming HTTP requests to the appropriate function endpoint managed by the Orchestrator.

Orchestrator: The brain of the platform, implemented as the main Django project. It is responsible for:

Managing function definitions and deployment versions.

Tracking the state of the worker pool and running function instances.

Making scheduling decisions (e.g., cold start vs. warm start).

Maintaining invocation logs and metrics.

Worker Pool: A collection of physical or virtual machines registered with the Orchestrator. Each worker runs one or more Function Instances.

Function Instance: The execution unit of the platform. Each instance is a single OS process running the runtime_host.py script, which in turn loads and executes a specific user function. Instances are HTTP servers that receive requests via the Gateway->Orchestrator chain.

2. Invocation Flow
Cold Start Invocation Flow
A cold start occurs when a function invocation request is received and no idle instances of that function are available.

Request Reception: The API Gateway (gateway app) receives a POST /invoke/{function_name}/ request.

Orchestrator Lookup: The Gateway queries the Orchestrator's database to find the requested function and its active deployment.

Instance Check: The Orchestrator checks its FunctionInstance table for a RUNNING or IDLE instance for the deployment. None is found.

Scheduling Decision: The Orchestrator selects a suitable WorkerNode from the pool based on resource availability (e.g., memory).

Instance Record Creation: The Orchestrator creates a new FunctionInstance record with status PENDING.

Process Spawning: The Orchestrator commands the chosen worker (e.g., via a message queue or agent) to start a new process. The command includes the deployment ID and the assigned port.

Runtime Startup: On the worker, a manager process (e.g., a custom manage.py command) executes:
USER_FUNCTION_PATH=/code/deployment_123.py python runtime_host.py

Function Loading: runtime_host.py starts, loads the user's function from the specified path, and begins listening on the configured port.

Registration: runtime_host.py signals back to the Orchestrator's /api/runtime/instance_ready/ endpoint that it is RUNNING.

Request Proxying: The Orchestrator informs the Gateway, which then proxies the original request to the new instance's URL (http://worker_ip:port/).

Execution & Response: The runtime_host.py receives the request, passes the body to the user's handle function, and returns the result. The Gateway relays this response back to the original client.

Warm Start Invocation Flow
A warm start occurs when an idle instance of the function is already available.

Steps 1-2: Identical to Cold Start.

Instance Found: The Orchestrator finds an existing FunctionInstance with status IDLE or RUNNING for the deployment.

Direct Proxying: The Orchestrator immediately returns the instance's URL to the Gateway, which proxies the request to it.

Execution & Response: Identical to Cold Start (Step 11). The instance's last_accessed field is updated.

The warm path is significantly faster as it eliminates the overhead of process creation, dependency installation, and interpreter startup.

3. The Core Technology Decision & Justification
Analysis: Container-based vs. Process-based Execution
For the execution layer of a lightweight internal FaaS platform, the choice between containers and bare processes is fundamental. Below is an analysis of the trade-offs.

Criteria	Container-based Approach (e.g., Docker)	Process-based Approach (Proposed)
Security Isolation	High. Strong isolation via kernel namespaces and cgroups.	Low to Medium. Relies on OS user permissions and security policies. Suitable for trusted internal code.
Resource Overhead	High. Each function invocation carries the overhead of a full container runtime and often a minimal OS layer.	Very Low. Only a Python process is spawned. Memory and CPU footprint are minimal.
Cold Start Performance	Slow. Image pulling (if not cached) and container startup add significant latency (>100ms).	Very Fast. Process forking or spawning is extremely fast on modern OSes (<10ms).
Implementation Complexity	High. Requires managing a container registry, image builds, and a container orchestrator (e.g., Kubernetes).	Low. Uses standard OS primitives (subprocess.Popen). Simple to build, debug, and manage.
Dependency Management	Robust. Dependencies are baked into the image, ensuring consistency.	Challenging. Requires a separate mechanism to install dependencies on workers before runtime (e.g., pip install -r requirements.txt on deployment).
Recommendation for AryaXAI
I strongly recommend a Process-based execution layer for AryaXAI's internal FaaS platform.

Justification:
Alignment with "Lightweight" and "Performance" Goals: The primary drivers for this project are "maximum performance" and "control." A process-based model delivers the lowest possible latency and resource overhead, directly translating to higher throughput and lower cost. Cold starts, a critical performance metric for FaaS, are minimized.

Reduced Implementation Complexity: This proof-of-concept, centered around runtime_host.py, demonstrates the approach's simplicity. We avoid the entire ecosystem of container management, which is a significant operational burden. The system is easier to reason about, debug, and secure for internal use.

Sufficient for Trusted Internal Code: The platform is intended for internal use. The threat model is different from a public cloud offering. While security is always important, the need for absolute kernel-level isolation is reduced when executing code from trusted internal developers. OS-level user isolation can provide a reasonable security boundary.

Faster Iteration and Development: Developers can test functions more rapidly without going through a container build/push cycle. The platform team can iterate on the core runtime and orchestrator faster without the complexity of integrating with Kubernetes or Docker.

Addressing the Trade-offs:
Security: We will mitigate the weaker isolation by running each function instance under a dedicated non-privileged OS user, leveraging filesystem permissions and leveraging security profiles (e.g., seccomp on Linux) where necessary.

Dependency Management: We will implement a robust deployment pipeline where the Orchestrator, upon receiving a new deployment, triggers a process to install dependencies on all workers (e.g., in a virtualenv located at /venvs/deployment_<id>). The runtime_host.py will then be configured to use the correct virtualenv. This is a solvable engineering challenge that is simpler than managing a container registry.

Conclusion: The process-based approach offers a superior balance of performance, simplicity, and control for an internal platform, making it the ideal choice for AryaXAI's specific context.