from fastapi import APIRouter, Depends

from lig.api.v1.arp import router as arp_router
from lig.api.v1.config import router as config_router
from lig.api.v1.devices import router as devices_router
from lig.api.v1.diagnostics import router as diagnostics_router
from lig.api.v1.facts import router as facts_router
from lig.api.v1.interfaces import router as interfaces_router
from lig.api.v1.mac import router as mac_router
from lig.api.v1.neighbors import router as neighbors_router
from lig.api.v1.routes import router as routes_router
from lig.security.authentication import get_current_user
from lig.security.rate_limit import check_rate_limit

api_v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(get_current_user), Depends(check_rate_limit)],
)

# Include all subrouters
api_v1_router.include_router(devices_router)
api_v1_router.include_router(facts_router)
api_v1_router.include_router(interfaces_router)
api_v1_router.include_router(routes_router)
api_v1_router.include_router(arp_router)
api_v1_router.include_router(mac_router)
api_v1_router.include_router(neighbors_router)
api_v1_router.include_router(config_router)
api_v1_router.include_router(diagnostics_router)
