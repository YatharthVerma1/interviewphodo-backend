from .tcs           import TCS_CONFIG
from .infosys       import INFOSYS_CONFIG
from .wipro         import WIPRO_CONFIG
from .hcl           import HCLTEC_CONFIG
from .accenture     import ACCENTURE_CONFIG
from .cognizant     import COGNIZANT_CONFIG
from .tech_mahindra import TECH_MAHINDRA_CONFIG
from .zoho          import ZOHO_CONFIG

COMPANY_CONFIGS = {
    "tcs":           TCS_CONFIG,
    "infosys":       INFOSYS_CONFIG,
    "wipro":         WIPRO_CONFIG,
    "hcl":           HCLTEC_CONFIG,
    "accenture":     ACCENTURE_CONFIG,
    "cognizant":     COGNIZANT_CONFIG,
    "tech_mahindra": TECH_MAHINDRA_CONFIG,
    "zoho":          ZOHO_CONFIG,
}

VALID_COMPANIES = list(COMPANY_CONFIGS.keys())

def get_company_config(company_id: str) -> dict:
    config = COMPANY_CONFIGS.get(company_id.lower())
    if not config:
        raise ValueError(
            f"Unknown company '{company_id}'. Valid options: {VALID_COMPANIES}"
        )
    return config
