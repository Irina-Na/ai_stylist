from typing import Dict, List, Optional
from pydantic import BaseModel, Field

TOTAL_CREATIONLOOK_PROMPT_v_0_1 = """\
You are a professional stylist creating a total look.
Here's the user request: {request}.
Analyze the request and put together a look that meets all the user's requirements.
The basic outfit should consist of top+bottom or full.
Also select shoes and bag. Add outerwear/accessories if needed.
Avoid watches, shawl, цветы.
One value can consist of only one word.
For sex use female, male, unisex. For the rest, use English only.
"""

# ---------- Pydantic models ----------
class Item(BaseModel):
    category: str
    color: Optional[str] = None
    fabric: Optional[str] = None
    pattern: Optional[str] = None
    detailes: Optional[str] = None


class Items(BaseModel):
    top: Optional[List[str]] = None
    bottom: Optional[str] = None
    full: Optional[str] = None
    shoes: Optional[str] = None
    bag: Optional[str] = None
    outerwear: Optional[List[str]] = None
    accessories: Optional[List[str]] = None


class OneTotalLook(BaseModel):
    sex: Optional[str] = None
    season: Optional[str] = None
    style: List[str] = Field(default_factory=list)
    fit: Optional[str] = None            # fitted | semi-fitted | oversized
    fabric: List[str] = Field(default_factory=list)
    material: List[str] = Field(default_factory=list)
    color_temperature: Optional[str] = None
    color_tone: Optional[str] = None
    pattern: List[str] = Field(default_factory=list)
    construction: List[str] = Field(default_factory=list)
    length: Optional[str] = None         # mini | midi | maxi
    garment_type: Optional[str] = None
    top: Optional[List[str]] = None
    bottom: Optional[List[str]] = None
    full: Optional[List[str]] = None
    shoes: Optional[List[str]] = None
    bag: Optional[List[str]] = None
    outerwear: Optional[List[str]] = None
    accessories: Optional[List[str]] = None
    items: Optional[List[Items]] = None


TOTAL_CREATIONLOOK_PROMPT = '''
You are a professional stylist creating a total look.
Analyze the user request and put together a look that meets all the user's requirements.
The basic outfit should include the top item + bottom item or instead full body item.
Also select shoes and bag. Add outerwear/accessories if needed.
If layering is necessary, add a few things of the appropriate type (example - top: ['tank top', 'shirt']).


### Instructions: Use **only** the exact enum values listed below.

### Global rules. 
• `sex` → `f` | `m` | `u`  (female, male, unisex).  
• `season`  → `summer` | `demi` | `winter`.
• `fit` → `fitted` | `semi-fitted` | `oversized`.
• `waist_fit` → `high`, `standart`, `low`.
• `length` → `mini`, `midi`, `maxi`.
• `color_temperature` →  `warm`| `cold` | `achromatic`.
• `color_tone` → `pastel` | `bright` | `muted` | `dark-shades` | `neutral-palette`.
• `pattern` → `no-print` | `abstract` | `animal` | `watercolor` | `checked` | `ethno` | `floral` | `geometric` | `lettering-emblem` | `military` | `polka-dot` | `crushed` | `draped` | `pleated`
(despite what it says about the shape, we will categorize it as a pattern, because having visible lines on the garment is also a pattern that should be taken into account to not overwhelm the look or make it interesting.
• `fabric` → angora, boucle, tweed, cashmere, chiffon, corduroy, cotton, crepe, cutout lace, eyelash, denim, fur, jacquard, knitwear, mohair, leather, linen, organza, suede,taffeta, velvet, wool, knitwear, mohair, fleece, boucle, nylon, silk, tweed, elasticized, gabardine, satin.
• `material` → `matte` | `semi-matte` | `shiny` | `rigid` | `structured` | `cozy` | `draping` | `thin` | `voluminous` | `textured` | `neutral-texture` | `unusual` | `high-tech`.
• `construction` → `simple` | `minimalistic` | `complex` | `pleats` | `draping` | `cut-outs` | `slits`.
All features above affect the outfit style. But they do not influence the style of a particular piece. Things put together, in one capsule or in one outfit, the way they are selected, dressed, styled - create a style.
• `style` one or a list of the following options: classic, bussiness-best, bussiness-casual, smart-casual, casual(base),  safari, military, marine, drama, romantic, feminine, jockey, dandy, retro, entic (boho), avant-garde.

• `top` →   
• `bottom` → 
• `full` → 
• `outerwear` → 
• `shoes` → 
• `bag` → 
• `accessories` → 
'''