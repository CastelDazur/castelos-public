# CastelOS Hardware Detection Pattern
# Demonstrates how the system classifies compute resources
# Actual sensor and tuning logic is private


class GPUBudgetController:
      """
          Prevents resource contention by enforcing limits on what can run
              concurrently on the GPU. Rules are based on task classes, not on
                  raw VRAM percentages.

                      The real system uses slot-based admission control:
                          each task class has a maximum number of concurrent GPU slots.
                              """

    # Slot limits by task class (illustrative, tunable via env vars)
      SLOT_LIMITS = {
          "critical": 1,         # Only one critical task on GPU at a time
          "heavy": 2,            # Two heavy tasks allowed concurrently
          "media": 2,            # Media generation gets its own lane
          "balanced": 3,         # Standard tasks share remaining capacity
          "throughput": 4,       # Lightweight tasks can run in parallel
      }

    def __init__(self):
              self.active_slots: dict[str, int] = {k: 0 for k in self.SLOT_LIMITS}

    def can_admit(self, task_class: str) -> bool:
              """Check if a new task of this class can be admitted to GPU."""
              limit = self.SLOT_LIMITS.get(task_class, 1)
              return self.active_slots.get(task_class, 0) < limit

    def admit(self, task_class: str) -> bool:
              """Try to reserve a GPU slot for this task class."""
              if not self.can_admit(task_class):
                            return False  # Route to CPU fallback or queue
        self.active_slots[task_class] = self.active_slots.get(task_class, 0) + 1
        return True

    def release(self, task_class: str):
              """Release a GPU slot when task completes."""
              current = self.active_slots.get(task_class, 0)
              self.active_slots[task_class] = max(0, current - 1)

    def get_routing_hint(self, task_class: str) -> str:
              """Suggest execution tier based on current GPU budget."""
              if self.can_admit(task_class):
                            return "gpu_hot"       # Run on GPU
elif task_class in ("balanced", "throughput"):
            return "cpu_service"   # Offload to CPU service lane
else:
            return "queued"        # Wait for GPU slot
