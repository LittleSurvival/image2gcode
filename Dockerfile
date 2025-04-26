# Dockerfile for image2gcode application
FROM python:3.13-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    libx11-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Install curl, then Rust/Cargo, then clean up apt lists
RUN apt-get update && apt-get install -y curl build-essential && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    rm -rf /var/lib/apt/lists/*

# Add cargo to PATH for subsequent commands in this build stage and the final container
ENV PATH="/root/.cargo/bin:${PATH}"

# Install svg2gcode-cli using cargo
RUN cargo install svg2gcode-cli

# Copy application code
COPY . /app

# Set environment to avoid Qt warnings
ENV QT_X11_NO_MITSHM=1

# Expose volume for output if needed
VOLUME ["/app/output"]

CMD ["python", "app.py"]