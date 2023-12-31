def import_MyWebScrapingTools():
  import importlib.machinery
  import requests
  # Fetch the raw content of the .py file.
  GitHub_url = 'https://raw.githubusercontent.com/LeonardoAcquaroli/MyWebScrapingTools/main/MyWebscrapingTools.py'
  response = requests.get(GitHub_url)
  response.raise_for_status()
  # Use importlib to import the .py file as a module.
  module_name = 'MyWsTools'
  loader = importlib.machinery.SourceFileLoader(module_name, 'MyWebscrapingTools.py')
  module = loader.load_module()
  return module
  
import_MyWebScrapingTools()
