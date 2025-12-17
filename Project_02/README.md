# ACL Rehab Tracker PCB (Project 2)

Compact PCB spin of the Project 1 ACL Rehab Tracker, prepared for fabrication and assembly. This folder holds all design sources and manufacturing outputs.

## Contents
- `ACL Rehab Tracker Schematics.pdf` – quick schematic reference.
- `Docs/` – PDF plots of top/bottom layers and routing.
- `EAGLE/` – editable EAGLE design files (`.sch`, `.brd`, and custom library).
- `ACL_Rehab_Tracker_BOM.csv` – bill of materials for sourcing parts.
- `MFG/CAMOutputs/` – production package:
  - `GerberFiles/` – copper, mask, paste, and silkscreen layers.
  - `DrillFiles/` – NC drill file.
  - `Assembly/` – pick-and-place (front/back) and assembly notes.

## How to build
1) Review the schematic PDF for component intent and placements.  
2) If editing, open `EAGLE/ACL_Rehab_Tracker.sch` and `.brd`, then regenerate CAM if changes are made.  
3) Zip `MFG/CAMOutputs/GerberFiles` and `DrillFiles` for PCB fab.  
4) Send `MFG/CAMOutputs/Assembly` files with the BOM to your assembler for PnP.  
5) Use the Project 1 firmware/software with this board; no firmware changes are required for a fab-only spin.

## Notes
- Designed as a compact, production-ready version of the original prototype.  
- Check part availability against `ACL_Rehab_Tracker_BOM.csv` before ordering to avoid substitutions.  
- If your fab expects a single archive, include the gerbers, drill, and both PnP files.

