# Export the three flexible wrist parts from adjustable-ft-v33.scad with OpenSCAD (Windows).
# Then run scripts/build_flexible_wrist_meshes.py in WSL.
#   powershell -File export_flexible_wrist_scad.ps1
$ErrorActionPreference = "Stop"
$exe = "C:\Program Files\OpenSCAD\openscad.com"
$src = Join-Path $PSScriptRoot "..\meshes\flexible_wrist\src"
$scad = Join-Path $src "adjustable-ft-v33.scad"
$parts = @{
    "scad_base"   = @("make_base_ring=true",  "make_hand_base_plate=false", "make_stopper_ring=false");
    "scad_top"    = @("make_base_ring=false", "make_hand_base_plate=true",  "make_stopper_ring=false");
    "scad_bottom" = @("make_base_ring=false", "make_hand_base_plate=false", "make_stopper_ring=true");
}
foreach ($name in $parts.Keys) {
    $args = @("-o", (Join-Path $src "$name.stl"), "-D", "make_test_cut=false", "-D", "explode_hand=0")
    foreach ($d in $parts[$name]) { $args += "-D"; $args += $d }
    $args += $scad
    & $exe @args
    if ($LASTEXITCODE -ne 0) { throw "openscad failed: $name" }
}
