# Low-Cost, Python-Controlled, Solvent-Resistant Fraction Collector for Automated Flow Synthesis 

## Overview
This repository contains all design files, firmware, and documentation for a **low-cost, modular, and solvent-resistant fraction collector** designed for use in **automated flow chemistry applications**.

Developed to address the limitations of commercial and open-source fraction collectors, especially in handling **organic solvents**. This system integrates seamlessly with flow reactors for unattended, reproducible fraction collection. Features include:
- Compatibility with common organic solvents (e.g. Tetrahydrofuran, Tolyene, Acetone, Chloroform, Ethyl Acetate, Isopropanol)
- Programmable 3-axis benchtop CNC platform for flexible configurations
- Drop-counting and real-time volume feedback for accurate collection
- Python-based control interface for full automation
- Compact design suitable for chemistry fume hoods
- Mininimal number of components and easy to assemble
- Total build cost: approximately **$1,000 USD**

---

## Assembly Guide

### Bill of Materials (BoM)
The BoM to construct the fraction collector is shown below. 

| **Item**       | **Manufacturer** | **Part No.**               | **Qty** | **Specifications**        | **Unit Cost (USD)** | **Notes**                              |
| -------------- | ---------------- | -------------------------- | ------: | ------------------------- | ------------------: | -------------------------------------- |
| CNC Router     | Genmitsu         | 3018-PROVer V2             |       1 | 425 × 352 × 300 mm        |             $228.65 | Main platform                          |
| Selector Valve | Runze Fluid      | QHF-SV04M-B-X-U-T10-K1.2-C |       1 | 10 Port or 6 Port         |             $414.00 | Switching between waste and collection |
| Drop Counter   | Vernier®         | GDX-DC                     |       1 | Go Direct®                |             $206.00 | For drop counting                      |
| Fixture        | N/A              | N/A                        |       1 | Custom 3D-Printed         |        $2.00 (est.) | For integrating modules                |
| Tubing         | IDEX             | 1502                       |   ≥5 ft | 1/16″ OD × 0.030″ ID, PFA |              $28.45 | Tubing                                 |
| Flangeless Nut | IDEX             | P-245                      |      ≥5 | 1/4-28, PFA               |          $3.36 each | Tubing connector                       |
| Ferrule        | IDEX             | P-200N                     |      ≥5 | 1/4-28 for 1/16″ OD, ETFE |          $1.79 each | Tubing connector                       |

### Mechanical Assembly

1. **CNC Platform Setup**
   - Assemble CNC frame per manufacturer instructions.
   - Mount custom vial tray or holder onto the platform.

2. **Selector Valve Integration**
   - Secure the selector valve near the fluid outlet line.
   - Route the waste and collection tubing through chemically resistant tubing into waste and collection vials.

3. **Drop Counter Installation**
   - Position the drop counter below the outlet nozzle.
   - Calibrate sensor height to detect single droplets accurately.

### Software & Control

- The fraction collector is controlled via a Python interface.

