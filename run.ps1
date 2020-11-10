Set-Location "$PSScriptRoot"
$Env:PYTHONPATH='src/main/python'
python src/main/python/main.py $args
