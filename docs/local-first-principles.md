# Local-first principles

CastelOS is built around a local-first mindset.
That does not mean "never use cloud."
It means the center of gravity stays under operator control.

## Design principle

In a local-first system:

- The workstation is the primary execution layer
- - Cloud services are optional and explicit, not default
  - - Data stays local unless there is a deliberate reason to move it
    - - The operator can audit, understand, and modify the execution path
      - - Reproducibility is built in, not retrofitted
       
        - ## Why that matters
       
        - - **Privacy:** No silent data movement or hidden logging
          - - **Repeatability:** Same inputs + same runtime = same outputs, always
            - - **Explicit runtime choices:** You pick which model, when, and for what reason
              - - **Fewer hidden dependencies:** No surprise API changes or service deprecations
                - - **Clearer upgrade path:** New runtimes are tested, approved, and reversible
                 
                  - ## Hardware as architecture
                 
                  - Local-first design also means respecting the hardware you actually use.
                 
                  - - What stays hot on GPU
                    - - What lives in RAM
                      - - What moves to slower storage or service layers
                        - - How workloads compete for resources
                          - - What bottlenecks appear under real load
                           
                            - This is not theoretical. It shapes the entire system.
                           
                            - ## Public note
                           
                            - This document describes principles only.
                            - It does not expose private implementation details or sensitive hardware tuning data.
