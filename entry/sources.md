# Sources

Reviewed for the Kubernetes deep-dive on **2026-09-05**. The source set intentionally prefers upstream Kubernetes documentation, canonical project repositories, and the standards/interfaces Kubernetes actually delegates to.

## Project and architecture

- **Kubernetes official site** — https://kubernetes.io/ (`official`)
- **Kubernetes source repository** — https://github.com/kubernetes/kubernetes (`repository`)
- **Kubernetes Components** — https://kubernetes.io/docs/concepts/overview/components/ (`documentation`)
- **Objects In Kubernetes** — https://kubernetes.io/docs/concepts/overview/working-with-objects/ (`documentation`)
- **Kubernetes API** — https://kubernetes.io/docs/concepts/overview/kubernetes-api/ (`documentation`)
- **API concepts** — https://kubernetes.io/docs/reference/using-api/api-concepts/ (`documentation`)
- **Controllers** — https://kubernetes.io/docs/concepts/architecture/controller/ (`documentation`)

## Workloads, scheduling, and resources

- **Pods** — https://kubernetes.io/docs/concepts/workloads/pods/ (`documentation`)
- **Deployments** — https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ (`documentation`)
- **StatefulSets** — https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ (`documentation`)
- **DaemonSets** — https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/ (`documentation`)
- **Jobs** — https://kubernetes.io/docs/concepts/workloads/controllers/job/ (`documentation`)
- **Kubernetes Scheduler** — https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/ (`documentation`)
- **Scheduling Framework** — https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/ (`documentation`)
- **Taints and Tolerations** — https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/ (`documentation`)
- **Pod Disruptions** — https://kubernetes.io/docs/concepts/workloads/pods/disruptions/ (`documentation`)
- **Resource Management for Pods and Containers** — https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ (`documentation`)
- **Liveness, Readiness, and Startup Probes** — https://kubernetes.io/docs/concepts/workloads/pods/probes/ (`documentation`)

## Networking and service discovery

- **Services, Load Balancing, and Networking** — https://kubernetes.io/docs/concepts/services-networking/ (`documentation`)
- **Services** — https://kubernetes.io/docs/concepts/services-networking/service/ (`documentation`)
- **EndpointSlices** — https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/ (`documentation`)
- **Network Policies** — https://kubernetes.io/docs/concepts/services-networking/network-policies/ (`documentation`)
- **Gateway API** — https://kubernetes.io/docs/concepts/services-networking/gateway/ (`documentation`)
- **Cluster Networking** — https://kubernetes.io/docs/concepts/cluster-administration/networking/ (`documentation`)

## Storage and runtimes

- **Volumes** — https://kubernetes.io/docs/concepts/storage/volumes/ (`documentation`)
- **Persistent Volumes** — https://kubernetes.io/docs/concepts/storage/persistent-volumes/ (`documentation`)
- **Storage Classes** — https://kubernetes.io/docs/concepts/storage/storage-classes/ (`documentation`)
- **Container Runtime Interface** — https://kubernetes.io/docs/concepts/containers/cri/ (`documentation`)
- **containerd CRI documentation** — https://github.com/containerd/containerd/blob/main/docs/cri/config.md (`documentation`)
- **OCI Runtime Specification** — https://specs.opencontainers.org/runtime-spec/ (`standard`)
- **OCI Image Specification** — https://specs.opencontainers.org/image-spec/ (`standard`)

## Security and policy

- **API Access Control** — https://kubernetes.io/docs/reference/access-authn-authz/ (`documentation`)
- **Authentication** — https://kubernetes.io/docs/reference/access-authn-authz/authentication/ (`documentation`)
- **Authorization** — https://kubernetes.io/docs/reference/access-authn-authz/authorization/ (`documentation`)
- **RBAC Authorization** — https://kubernetes.io/docs/reference/access-authn-authz/rbac/ (`documentation`)
- **Admission Controllers** — https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/ (`documentation`)
- **Pod Security Admission** — https://kubernetes.io/docs/concepts/security/pod-security-admission/ (`documentation`)
- **Secrets** — https://kubernetes.io/docs/concepts/configuration/secret/ (`documentation`)
- **Service Accounts** — https://kubernetes.io/docs/concepts/security/service-accounts/ (`documentation`)

## Reliability, operations, and upgrades

- **Operating etcd clusters for Kubernetes** — https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/ (`documentation`)
- **Highly Available Clusters with kubeadm** — https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/high-availability/ (`documentation`)
- **Upgrading kubeadm clusters** — https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/ (`documentation`)
- **Version Skew Policy** — https://kubernetes.io/releases/version-skew-policy/ (`documentation`)
- **Cluster Logging Architecture** — https://kubernetes.io/docs/concepts/cluster-administration/logging/ (`documentation`)
- **System Metrics** — https://kubernetes.io/docs/reference/instrumentation/metrics/ (`documentation`)

These links are evidence for the stable mental model and the version-sensitive operational details in the module. Feature states, defaults, supported version skew, API maturity, and upgrade procedures should be rechecked against the documentation for the Kubernetes release actually being operated.