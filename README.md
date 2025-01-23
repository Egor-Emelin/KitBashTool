# KitBashTool
Tool for converting KitBash assets to USD format. Works fbx files, hip files and Cargo imported assets.  
Select subnets(geo or subnet type nodes) on /obj level and run the script.  
To run the script i created shelf tool with the following code:
###
import hou  
from importlib import reload  
import sys  
from KitBashTool import KitBashTool # folder named KitBashTool with python file named KitBashTool  
sys.path.append("Your path to folder") # do this if your folder location is not in PYTHONPATH Houdini environment variable  
reload(KitBashTool)  
template = KitBashTool.KitBashTool()  
template.getData()  
template.USDexport('Your path for assets to save to')  
template.refImport('Your path for importing USD assets through reference node')  
###

There are 3 main functions getData(), USDexport(), refImport()    
You can only create templates with getData(), or run all 3 functions to have saved USD files and reference node with those files.  
