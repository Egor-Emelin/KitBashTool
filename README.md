# KitBashTool
Tool for converting KitBash assets to USD format. Works with FBX files, HIP files, and Cargo-imported assets.  
Select subnets (geo or subnet-type nodes) at the /obj level and run the script.  
To run the script, I created a shelf tool with the following code:
```python
import hou  
from importlib import reload  
import sys  
from KitBashTool import KitBashTool # folder named KitBashTool with python file named KitBashTool  
sys.path.append("Your path to folder") # Do this if your folder location is not in PYTHONPATH Houdini environment variable  
reload(KitBashTool)  
template = KitBashTool.KitBashTool()  
template.getData()  
template.USDexport('Your path for assets to save to')  
template.refImport('Your path for importing USD assets through reference node')  
```

There are 3 main functions: `getData()`, `USDexport()`, and `refImport()`.  
You can either create templates using `getData()`, or run all 3 functions to generate USD files and a reference node with those files.

