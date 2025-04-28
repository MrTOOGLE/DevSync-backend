FROM python:3.12

SHELL ["/bin/bash", "-c"]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKDIR_PATH="/backend" \
    VENV_PATH="/opt/venv"

ARG USERNAME=appuser

RUN useradd -ms /bin/bash ${USERNAME} \
    && mkdir -p ${WORKDIR_PATH} ${VENV_PATH} \
    && chown -R ${USERNAME} ${WORKDIR_PATH} ${VENV_PATH}

WORKDIR ${WORKDIR_PATH}

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

RUN uv venv ${VENV_PATH}
ENV PATH="${VENV_PATH}/bin:$PATH"

COPY --chown=${USERNAME} ./requirements.txt ./requirements.txt

RUN uv pip install --no-cache --require-hashes --requirements ./requirements.txt \
    && chown -R ${USERNAME} ${VENV_PATH}

COPY --chown=${USERNAME} ./ ./

USER ${USERNAME}
