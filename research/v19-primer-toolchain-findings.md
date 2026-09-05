# R-PrimerToolchain findings — free-first toolchain facts (v1.9 primer input)

Research ticket: earledotpy/skilltrace#165 (child of map #163).
Scope: facts only. No decisions. All claims cite the primary source that owns them.

## 1. Container runtimes: install shape, free-first standing, CI-testability

### 1a. Docker Engine (map Notes assume canonical)

- Install shape: native Linux install per distro (Ubuntu, Debian, Fedora, RHEL,
  CentOS, Raspberry Pi OS, static binaries); Docker Desktop is the separate
  macOS/Windows/Linux GUI distribution.
  Source: https://docs.docker.com/engine/install/
- Free-first standing: Docker Engine is an open-source project (Moby,
  Apache License 2.0); Docker provides no paid support for Engine itself.
  The paid-subscription gate applies to Docker Desktop / Docker products in
  larger enterprises (> 250 employees OR > $10M annual revenue), not to Engine.
  Sources: https://docs.docker.com/engine/install/ (Support, Licensing);
  https://docs.docker.com/desktop/setup/install/windows-install/ (Docker Desktop terms);
  https://docs.docker.com/subscription/
- CI-testability: GitHub-hosted `ubuntu-24.04` runners preinstall Docker Client
  28.0.4, Docker Server 28.0.4, Compose 2.38.2, Buildx 0.36.1 — `docker build` /
  `docker run` work with zero setup on stock CI.
  Source: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md
- Assessment vs map Notes: assumption CONFIRMED with evidence — Engine is the
  only option that is simultaneously free-standing (no seat/subscription gate),
  native on Linux CI, and preinstalled on GitHub-hosted runners.

### 1b. Podman

- Install shape: `dnf`/`apt`/`zypper`/`pacman`/`apk` per distro
  (Fedora/RHEL/CentOS Stream ship or support it; Debian 11+, Ubuntu 20.10+);
  macOS/Windows via `podman machine init/start` (VM-backed); listens for Docker
  API clients so Docker-based tooling mostly works.
  Source: https://podman.io/docs/installation
- Free-first standing: fully free and open-source (no subscription tier at all).
- CI-testability: present on GitHub-hosted `ubuntu-24.04` runners
  (Podman 5.8.4, plus Buildah 1.33.7, Skopeo 1.13.3 preinstalled), so a
  Podman-compat check is CI-runnable — but it is the secondary entry in the
  runner image, not the default container service.
  Source: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md
- Assessment: viable documented alternate; not canonical (Docker-API emulation
  layer, machine-VM indirection on desktop OSes).

### 1c. Rancher Desktop (SUSE)

- Install shape: Electron desktop app; download-and-run installer for
  macOS/Windows, package-manager install on Linux; wraps a VM (macOS/Linux) or
  WSL2 (Windows) running containerd or Docker + Kubernetes; bundles
  docker, nerdctl, kubectl, helm out of the box.
  Source: https://rancherdesktop.io/
- Free-first standing: open-source project (SUSE Rancher Engineering),
  no license fee.
- CI-testability: desktop GUI application — not designed as a headless CI
  service and not preinstalled on GitHub-hosted runners. Alternate for local
  dev only.
- Assessment: viable documented alternate; not CI-testable as canonical.

### 1d. Finch (AWS, open source)

- Install shape: simple native installer bundling nerdctl + containerd +
  BuildKit (OCI builds) + Lima-managed VM; macOS (Intel/Apple Silicon),
  Windows, Linux; CLI mirrors top-level `docker run`-style commands plus
  Compose; explicitly NOT a drop-in Docker replacement (project advises against
  aliasing) and NOT for production/multi-tenant use.
  Sources: https://runfinch.com/ ; https://github.com/runfinch/finch ;
  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-finch.html
- Free-first standing: free, open source (Apache License 2.0).
- CI-testability: AWS SAM CLI treats Finch as fallback when Docker is absent
  (Docker prioritized when both run) — same pattern: Docker is the default
  check target, Finch the alternate.
  Source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-finch.html
- Assessment: viable documented alternate; not CI-testable as canonical.

### 1e. Colima

- Install shape: macOS/Linux minimal-setup CLI (`brew install colima`,
  MacPorts/Nix/Mise); Lima-backed VM; default runtime Docker (requires separate
  `docker` client), also containerd/nerdctl, Incus, optional Kubernetes;
  `colima start` then plain `docker run`.
  Source: https://github.com/abiosoft/colima
- Free-first standing: free, open source (MIT).
- CI-testability: community tool aimed at macOS local dev; not preinstalled on
  GitHub-hosted runners; no headless-CI role.
- Assessment: viable documented alternate (macOS Docker Desktop replacement);
  not CI-testable as canonical.

### 1f. Docker Desktop — explicitly NOT the default (matches map Notes)

- Free only for small business (< 250 employees AND < $10M revenue), personal
  use, education, non-commercial open source; otherwise paid subscription
  required; government entities always require paid.
  Source: https://docs.docker.com/desktop/setup/install/windows-install/
- Assessment: confirms the map Notes stance — Desktop is not the free-first
  default; Engine is.

## 2. FastAPI minimal primer scope (official docs)

- Smallest app: one `main.py` —
  `from fastapi import FastAPI`, `app = FastAPI()`,
  `@app.get("/")` returning `{"message": "Hello World"}`;
  serve dev via `fastapi dev`, serve production via `fastapi run`
  (Uvicorn underneath); interactive docs free at `/docs` (Swagger UI),
  `/redoc`, raw schema at `/openapi.json`.
  Source: https://fastapi.tiangolo.com/tutorial/first-steps/
- Primer Dockerfile (canonical, from-scratch, no base image): official Python
  image, `WORKDIR /code`, copy `requirements.txt` first (layer cache),
  `pip install --no-cache-dir --upgrade -r`, copy `./app` last (changes most),
  exec-form `CMD ["fastapi", "run", "app/main.py", "--port", "80"]`
  (exec form required for graceful shutdown/lifespan; add `--proxy-headers`
  behind Nginx/Traefik); single-file variant copies `./main.py` to `/code/`.
  The old `tiangolo/uvicorn-gunicorn-fastapi` base image is deprecated — do not
  use. Build/run: `docker build -t myimage .` /
  `docker run -d --name mycontainer -p 80:80 myimage`.
  Source: https://fastapi.tiangolo.com/deployment/docker/
- Minimal primer scope derivable from the above (facts, not a scope decision):
  single-file or `app/` layout + requirements + Dockerfile + build/run/smoke
  (`curl /` and `/docs`) commands.

## 3. HF Spaces ZeroGPU deploy path (capstone input)

- ZeroGPU = shared dynamic GPU allocation (NVIDIA RTX Pro 6000 Blackwell;
  `large` = half card/48GB default, `xlarge` = full/96GB at 2x quota);
  request/release per-call via `import spaces` + `@spaces.GPU`
  (effect-free outside ZeroGPU envs); models placed on `cuda` at module level;
  Gradio 4+, PyTorch 2.8.0–latest, Python 3.10.13/3.12.12; no `torch.compile`
  (AOT only); durations default 60s, configurable, shorter = better queue
  priority.
  Source: https://huggingface.co/docs/hub/en/spaces-zerogpu
- Free-first hosting: free personal accounts in good standing (verified email,
  account older than 30 days) can host up to 2 ZeroGPU Spaces; PRO up to 10;
  Team/Enterprise orgs up to 50. Usage quotas per day: unauthenticated 2 min,
  free 5 min (medium priority), PRO/Team/Enterprise 40–60 min (highest,
  extensible via $1/10min credits).
  Source: https://huggingface.co/docs/hub/en/spaces-zerogpu
- Hard constraint for the primer/capstone: ZeroGPU is exclusively compatible
  with the Gradio SDK. Gradio and Docker Spaces otherwise run on compute that
  requires a paid plan (PRO personal / Team or Enterprise org); Static Spaces
  are the only unconditionally free SDK. Docker-image deploy is therefore NOT
  a free-first path; the free-first GPU capstone path is Gradio + ZeroGPU
  (+ `@spaces.GPU`), with the container primer covering local Engine
  build/run and Gradio covering hosted deploy.
  Source: https://huggingface.co/docs/hub/en/spaces-overview ;
  https://huggingface.co/docs/hub/en/spaces-zerogpu (Compatibility)

## 4. Canonical-target evidence summary (for the primer decision ticket)

- Map Notes assume Docker Engine canonical — CONFIRMED: Engine is Apache-2.0
  free with no subscription gate, installs natively on Linux CI, and is
  preinstalled (client+server+compose+buildx) on GitHub-hosted runners.
- Podman is the only alternate that is also CI-present (preinstalled
  5.8.4) — candidate compat-note, not canonical.
- Rancher Desktop / Finch / Colima are all free and open-source but are
  local-dev tools with no headless-CI preinstall — alternates section only.
- Docker Desktop stays non-default (subscription gate above the SME threshold).
- FastAPI primer floor = official from-scratch Dockerfile + build/run/smoke.
- Spaces free-first GPU path = Gradio SDK + ZeroGPU (max 2 spaces, 5 min/day
  on free); Docker Spaces need a paid plan.
