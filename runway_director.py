"""
AI Runway Director - Backend module for 3D runway visualization
Handles scene configuration, image processing, and director command parsing
"""

from __future__ import annotations
import os
import base64
import io
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
import requests
from PIL import Image
import cerebras.cloud.sdk as cerebras
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------- helpers ----------
def _get_cerebras_api_key() -> Optional[str]:
    return os.getenv("API_KEY_CEREBRAS") or os.getenv("CEREBRAS_API_KEY")

def _extract_message_content(response) -> str:
    if not response or not getattr(response, "choices", None):
        raise ValueError("API returned no choices")
    message = response.choices[0].message
    if not message:
        raise ValueError("API returned no message")
    content = message.content
    if content is None:
        raise ValueError("API returned None content")
    if not isinstance(content, str):
        content = str(content)
    content = content.strip()
    if not content:
        raise ValueError("API returned empty content")
    return content

# ---------- Pydantic Models ----------

class RunwayItem(BaseModel):
    """Single item displayed on the runway"""
    id: str
    name: str
    category: str
    image_url: Optional[str] = None
    image_data_uri: Optional[str] = None
    price: Optional[float] = None
    brand: Optional[str] = None
    store_id: Optional[str] = None
    good_id: Optional[str] = None

class CoverConfig(BaseModel):
    """Vogue-style cover overlay configuration"""
    title: str = "VOGUE"
    subtitle: str = "Collection 2026"
    badges: List[str] = Field(default_factory=list)

class SceneConfig(BaseModel):
    """3D scene configuration"""
    preset: str = "minimal"
    fog_density: float = 0.02
    fog_color: str = "#000000"
    background_color: str = "#111111"
    spotlight_intensity: float = 1.0
    spotlight_color: str = "#ffffff"
    particle_count: int = 500
    particle_speed: float = 0.001
    camera_distance: float = 15
    camera_height: float = 5
    theme: str = "minimal"
    lighting: str = "soft"
    atmosphere: str = "clean"

class TransitionConfig(BaseModel):
    """Animation transition effects"""
    effects: List[str] = Field(default_factory=list)

class DirectorCommand(BaseModel):
    """Complete director command from LLM"""
    scene: SceneConfig
    cover: CoverConfig
    transitions: TransitionConfig

class RunwayScene(BaseModel):
    """Complete runway scene package"""
    items: List[RunwayItem]
    cover: CoverConfig
    scene: SceneConfig
    transitions: TransitionConfig = Field(default_factory=TransitionConfig)

# ---------- Scene Presets ----------

SCENE_PRESETS = {
    "paris_runway": {
        "preset": "paris_runway",
        "fog_density": 0.015,
        "fog_color": "#1a1a1a",
        "background_color": "#2a2a2a",
        "spotlight_intensity": 0.8,
        "spotlight_color": "#fff5e6",
        "particle_count": 300,
        "particle_speed": 0.0005,
        "camera_distance": 18,
        "camera_height": 6,
        "theme": "Paris Runway",
        "lighting": "Warm Soft",
        "atmosphere": "Elegant Minimal"
    },
    "cyberpunk": {
        "preset": "cyberpunk",
        "fog_density": 0.04,
        "fog_color": "#0a0a1a",
        "background_color": "#050510",
        "spotlight_intensity": 1.5,
        "spotlight_color": "#7cffd1",
        "particle_count": 800,
        "particle_speed": 0.003,
        "camera_distance": 12,
        "camera_height": 3,
        "theme": "Cyberpunk Tokyo",
        "lighting": "Neon",
        "atmosphere": "Futuristic Rain"
    },
    "editorial_90s": {
        "preset": "editorial_90s",
        "fog_density": 0.005,
        "fog_color": "#ffffff",
        "background_color": "#ffffff",
        "spotlight_intensity": 1.2,
        "spotlight_color": "#ffffff",
        "particle_count": 200,
        "particle_speed": 0.0002,
        "camera_distance": 20,
        "camera_height": 8,
        "theme": "Editorial 90s",
        "lighting": "High Contrast",
        "atmosphere": "Clean Minimal"
    },
    "red_carpet": {
        "preset": "red_carpet",
        "fog_density": 0.01,
        "fog_color": "#1a0000",
        "background_color": "#0a0000",
        "spotlight_intensity": 2.0,
        "spotlight_color": "#ffffff",
        "particle_count": 400,
        "particle_speed": 0.001,
        "camera_distance": 14,
        "camera_height": 4,
        "theme": "Red Carpet",
        "lighting": "Dramatic Spots",
        "atmosphere": "Glamorous"
    },
    "minimal": {
        "preset": "minimal",
        "fog_density": 0.02,
        "fog_color": "#000000",
        "background_color": "#111111",
        "spotlight_intensity": 1.0,
        "spotlight_color": "#ffffff",
        "particle_count": 500,
        "particle_speed": 0.001,
        "camera_distance": 15,
        "camera_height": 5,
        "theme": "Minimal",
        "lighting": "Soft",
        "atmosphere": "Clean"
    }
}

# ---------- Image Processing ----------

def download_image(url: str, timeout: int = 10) -> Optional[bytes]:
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def resize_image(image_data: bytes, max_size: tuple = (400, 400)) -> bytes:
    """Resize image to specified max dimensions"""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except Exception as e:
        print(f"Error resizing image: {e}")
        return image_data

def image_to_data_uri(image_data: bytes, image_format: str = 'image/jpeg') -> str:
    """Convert image bytes to data URI"""
    base64_str = base64.b64encode(image_data).decode('utf-8')
    return f"data:{image_format};base64,{base64_str}"

def process_item_image(item: Dict[str, Any], max_size: tuple = (400, 400)) -> Optional[str]:
    """
    Process item image: download, resize, convert to data URI
    Returns data URI string or None if failed
    """
    image_url = item.get('image_external_url')
    if not image_url:
        return None
    
    # Download image
    image_data = download_image(image_url)
    if not image_data:
        return None
    
    # Resize image
    resized_data = resize_image(image_data, max_size)
    
    # Convert to data URI
    return image_to_data_uri(resized_data)

# ---------- Scene Building ----------

def build_runway_scene(
    items_data: List[Dict[str, Any]],
    preset: str = "minimal",
    cover_title: str = "VOGUE",
    cover_subtitle: str = "Collection 2026",
    cover_badges: Optional[List[str]] = None
) -> RunwayScene:
    """
    Build a complete runway scene from filtered dataset items
    
    Args:
        items_data: List of item dictionaries from filtered dataset
        preset: Scene preset name
        cover_title: Cover title
        cover_subtitle: Cover subtitle
        cover_badges: List of cover badges
    
    Returns:
        RunwayScene object with all configuration
    """
    # Process items
    runway_items = []
    for idx, item in enumerate(items_data):
        # Process image
        image_data_uri = process_item_image(item)
        
        # Extract category from key if available
        category = item.get('category', 'Item')
        
        runway_item = RunwayItem(
            id=str(idx),
            name=item.get('name', 'Unknown'),
            category=category,
            image_url=item.get('image_external_url'),
            image_data_uri=image_data_uri,
            price=item.get('price'),
            brand=item.get('brand'),
            store_id=item.get('store_id'),
            good_id=item.get('good_id')
        )
        runway_items.append(runway_item)
    
    # Get scene preset
    scene_config_dict = SCENE_PRESETS.get(preset, SCENE_PRESETS["minimal"])
    scene_config = SceneConfig(**scene_config_dict)
    
    # Build cover
    cover = CoverConfig(
        title=cover_title,
        subtitle=cover_subtitle,
        badges=cover_badges or []
    )
    
    # Build complete scene
    scene = RunwayScene(
        items=runway_items,
        cover=cover,
        scene=scene_config,
        transitions=TransitionConfig()
    )
    
    return scene

# ---------- Director LLM Integration ----------

DIRECTOR_PROMPT = """You are a fashion show director creating a runway presentation.

Given the user's director command, generate a JSON response with scene, cover, and transition configurations.

User command: {command}

Generate a JSON response with this exact structure:
{{
  "scene": {{
    "preset": "paris_runway|cyberpunk|editorial_90s|red_carpet|minimal",
    "fog_density": 0.0-0.1,
    "fog_color": "#hexcolor",
    "background_color": "#hexcolor",
    "spotlight_intensity": 0.5-3.0,
    "spotlight_color": "#hexcolor",
    "particle_count": 100-1000,
    "particle_speed": 0.0001-0.01,
    "camera_distance": 10-25,
    "camera_height": 2-10,
    "theme": "string",
    "lighting": "string",
    "atmosphere": "string"
  }},
  "cover": {{
    "title": "string (uppercase, 2-3 words max)",
    "subtitle": "string (short phrase)",
    "badges": ["badge1", "badge2"]
  }},
  "transitions": {{
    "effects": ["fade", "glitch", "neon_pulse", "zoom", "slide"]
  }}
}}

Guidelines:
- Choose preset based on command keywords (Paris, cyberpunk, Tokyo, 90s, red carpet, etc.)
- Adjust fog, lighting, and camera to match the mood
- Create compelling cover title and subtitle
- Add relevant badges (e.g., "waterproof", "office-to-party", "statement piece")
- Include 1-3 transition effects

Return ONLY valid JSON, no other text.
"""

def parse_director_command(command: str, model: str = "zai-glm-4.7") -> Optional[DirectorCommand]:
    """
    Parse natural language director command into structured configuration
    
    Args:
        command: Natural language director command
        model: LLM model to use
    
    Returns:
        DirectorCommand object or None if parsing fails
    """
    try:
        api_key = _get_cerebras_api_key()
        if not api_key:
            print("API_KEY_CEREBRAS/CEREBRAS_API_KEY not found")
            return None
        
        client = cerebras.Cerebras(api_key=api_key)
        
        messages = [
            {"role": "system", "content": DIRECTOR_PROMPT.format(command=command)}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        content = _extract_message_content(response)
        
        # Try to extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        import json
        command_dict = json.loads(content)
        
        return DirectorCommand(**command_dict)
        
    except Exception as e:
        print(f"Error parsing director command: {e}")
        return None

# ---------- HTML Generation ----------

def generate_runway_html(scene: RunwayScene, widget_path: str = "ui/runway_widget.html") -> str:
    """
    Generate HTML for runway widget with scene data injected
    
    Args:
        scene: RunwayScene object
        widget_path: Path to the base HTML widget template
    
    Returns:
        Complete HTML string with scene data
    """
    try:
        # Read base template
        template_path = Path(__file__).parent / widget_path
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Convert scene to JSON
        scene_json = scene.model_dump_json(indent=2)
        
        # Inject scene data into HTML
        # Add script to initialize scene with data
        init_script = f"""
        <script>
        // Scene data injected from Python
        const runwaySceneData = {scene_json};
        
        // Initialize scene with data when ready
        window.addEventListener('load', function() {{
            if (typeof addItemsToRunway === 'function' && runwaySceneData.items) {{
                addItemsToRunway(runwaySceneData.items);
            }}
            if (typeof updateScene === 'function' && runwaySceneData.scene) {{
                updateScene(runwaySceneData.scene);
            }}
            if (typeof updateCover === 'function' && runwaySceneData.cover) {{
                updateCover(
                    runwaySceneData.cover.title,
                    runwaySceneData.cover.subtitle,
                    runwaySceneData.cover.badges
                );
            }}
        }});
        </script>
        """
        
        # Insert before closing body tag
        html = html.replace('</body>', init_script + '</body>')
        
        return html
        
    except Exception as e:
        print(f"Error generating runway HTML: {e}")
        return f"<div>Error generating runway: {str(e)}</div>"

# ---------- Utility Functions ----------

def get_available_presets() -> List[str]:
    """Get list of available scene presets"""
    return list(SCENE_PRESETS.keys())

def get_preset_description(preset: str) -> Optional[str]:
    """Get description of a preset"""
    preset_data = SCENE_PRESETS.get(preset)
    if preset_data:
        return f"{preset_data['theme']} - {preset_data['lighting']} lighting, {preset_data['atmosphere']} atmosphere"
    return None
