Set-Location "$PSScriptRoot"
$Env:PYTHONPATH='src/main/python'
if ($Env:WORKON_HOME) {
	$PYTHON="$Env:WORKON_HOME\photocopieuse\Scripts\pythonw.exe"
} else {
	$PYTHON="python"
}
& "$PYTHON" src/main/python/main.py $args
