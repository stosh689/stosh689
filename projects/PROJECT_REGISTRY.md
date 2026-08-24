Stosh689 Project Registry

Purpose

This repository contains multiple research and software projects. Each project must remain independently testable while sharing common infrastructure where appropriate.

Active Projects

CIDAR

Computational imaging, detection, ranging, confidence estimation, sensor fusion, uncertainty analysis, and related research.

Path:

projects/cidar/

GEDT

Global Economic Digital Twin for computational economic simulation, innovation modeling, statistical analysis, calibration, optimization, and reproducible experiments.

Path:

projects/gedt/

AI/ML

General artificial intelligence, machine learning, computer vision, neural networks, and model experimentation that is not specific to another project.

Path:

projects/ai_ml/

Disaster Response / GDRRP

Global disaster resilience and response systems, including data processing, resource coordination, sensing, and decision-support components.

Path:

projects/disaster_response/

Economic Simulation

Economic modeling and simulation components that may eventually become part of GEDT but are not yet sufficiently integrated.

Path:

projects/economic_simulation/

Experimental

Unfinished prototypes and research experiments that are worth preserving but are not currently production candidates.

Path:

projects/experimental/

Shared Infrastructure

Reusable components belong under:

shared/

Subdirectories:

* shared/data/
* shared/validation/
* shared/visualization/
* shared/utilities/
* shared/testing/

Documentation

Project-independent documentation belongs under:

docs/

Recommended documents:

* docs/ARCHITECTURE.md
* docs/ROADMAP.md
* docs/VALIDATION.md
* docs/RESEARCH.md

Testing

Project-specific tests belong with their respective projects.

Repository-wide integration tests belong under:

tests/integration/

Benchmarks

Performance and scalability experiments belong under:

benchmarks/

Scripts

Maintenance, migration, data preparation, and development scripts belong under:

scripts/

GitHub Actions

Continuous integration workflows belong under:

.github/workflows/

Organization Rules

1. Do not delete working code during migration.
2. Do not modify a passing workflow unless the change is necessary.
3. Move one project at a time.
4. Run tests after every migration.
5. Remove duplicate implementations only after the replacement has passed.
6. Keep project-specific dependencies isolated where practical.
7. Shared code must not depend on a single project.
8. Every active project must have its own README.
9. Every active project must have tests.
10. Experimental code must be clearly separated from production candidates.

Migration Order

1. Establish project registry.
2. Inventory existing files.
3. Organize GEDT.
4. Organize CIDAR.
5. Organize AI/ML.
6. Organize Disaster Response/GDRRP.
7. Organize Economic Simulation.
8. Separate experimental work.
9. Establish shared infrastructure.
10. Consolidate testing and CI.
11. Run the complete repository test suite.

Safety Principle

The current passing baseline is protected.

Organization must improve structure without 
sacrificing verified 

projects/
projects/cidar/
projects/gedt/
projects/ai_ml/
projects/disaster_response/
projects/economic_simulation/
projects/experimental/

shared/
shared/data/
shared/validation/
shared/visualization/
shared/utilities/
shared/testing/

docs/
tests/integration/
benchmarks/
scripts/




