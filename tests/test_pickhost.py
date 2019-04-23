import subprocess
from pypick import Pick

def test_basic():
    subprocess.call(['pickhost', '-f', 'tests/hosts'])
