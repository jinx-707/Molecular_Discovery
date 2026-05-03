from prefect.settings import PREFECT_API_URL
from prefect.blocks.core import Block
from prefect.blocks.system import String
import os

# Prefect settings
PREFECT_API_URL.value("http://127.0.0.1:4200/api")  # local server

# Storage block for intermediate results
@Block.register(name="mol-discovery-results")
class MolDiscoveryResults(Block):
    storage_path: str = "/tmp/prefect_results"

# Concurrency limits
os.environ["PREFECT__FLOWS__RUNNERS__ML_QUEUE__MAX_CONCURRENT"] = "4"

# Result persistence
PREFECT_RESULTS_DEFAULT_SERIALIZER = "pickle"

print("Prefect configured for local development")

