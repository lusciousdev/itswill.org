from uvicorn.workers import UvicornWorker

class CustomWorker(UvicornWorker):
  CONFIG_KWARGS = { "lifespan" : "off" }
