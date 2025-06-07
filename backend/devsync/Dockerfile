FROM --platform=linux/amd64 python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKDIR_PATH="/backend" \
    VENV_PATH="/opt/venv"

ARG USERNAME=appuser

RUN apt-get update && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

RUN useradd -ms /bin/bash ${USERNAME} \
    && mkdir -p ${WORKDIR_PATH} ${VENV_PATH} \
    && chown -R ${USERNAME}:${USERNAME} ${WORKDIR_PATH} ${VENV_PATH} \
    && chmod -R 755 ${WORKDIR_PATH} ${VENV_PATH}

WORKDIR ${WORKDIR_PATH}

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

RUN uv venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:$PATH"

COPY --chown=${USERNAME}:${USERNAME} ./requirements.txt ./

RUN uv pip install --no-cache --require-hashes --requirements ./requirements.txt \
    && chown -R ${USERNAME}:${USERNAME} ${VENV_PATH} \
    && chmod -R 755 ${VENV_PATH}

COPY --chown=${USERNAME}:${USERNAME} ./ ./

USER ${USERNAME}