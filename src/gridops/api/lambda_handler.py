from mangum import Mangum

from gridops.api.main import app


handler = Mangum(app)