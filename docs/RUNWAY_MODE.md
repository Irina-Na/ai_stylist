# AI Runway Director - Documentation

## Overview

The **AI Runway Director** is a new feature that transforms your selected fashion looks into cinematic 3D runway presentations. Users can control lighting, camera, atmosphere, and cover styling through natural language commands.

## Features

### 🎬 3D Runway Visualization
- **WebGL-powered 3D scene** rendered in the browser (no GPU required on backend)
- **Interactive runway** with animated items, particles, and atmospheric effects
- **Vogue-style cover overlay** with customizable titles and badges

### 🎨 Scene Presets
Five professionally designed presets:
1. **Paris Runway** - Warm soft lighting, elegant minimal atmosphere
2. **Cyberpunk Tokyo** - Neon lights, futuristic rain atmosphere
3. **Editorial 90s** - High contrast, clean white background
4. **Red Carpet** - Dramatic spotlights, glamorous atmosphere
5. **Minimal** - Clean, soft lighting, neutral atmosphere

### 🎭 Director Commands
Natural language commands to control the scene:
- "Make it like Paris Fashion Week, minimalism, soft light"
- "Now cyberpunk Tokyo, rain, neon, camera closer"
- "Make an editorial 90s cover: large font, white background, grain"

## How to Use

### Step 1: Generate a Look
1. Go to the **Look Generator** tab
2. Enter your fashion brief (e.g., "I need a graduation look in soft pastel tones, summer, female")
3. Click "Сгенерировать лук" (Generate Look)
4. Review the two generated looks

### Step 2: Select and Send to Runway
1. Choose your preferred look (Look 1 or Look 2)
2. Click **"🎬 Показать на подиуме"** (Show on Runway)
3. The selected items will be saved for the runway

### Step 3: Customize the Scene
1. Switch to the **Runway Director** tab
2. **Choose a preset** from the dropdown menu
3. **Enter a director command** (optional) for custom styling
4. Click **"🎬 Применить команду"** to apply changes

### Step 4: Enjoy the Show
- Watch your items displayed as holographic cards on the 3D runway
- See the animated particles and lighting effects
- View the Vogue-style cover overlay

## Technical Architecture

### Backend (Python)
- **`runway_director.py`** - Core module for scene management
  - Image processing (download, resize, convert to base64)
  - Scene preset management
  - LLM integration for director command parsing
  - HTML generation with data injection

### Frontend (HTML/JavaScript)
- **`ui/runway_widget.html`** - Three.js-based 3D scene
  - WebGL rendering via Three.js
  - Dynamic scene updates
  - Item card overlays
  - Particle effects and animations

### Data Flow
```
User Input → LLM → Look Generation → SKU Matching → 
Scene Building → Image Processing → HTML Generation → 
Streamlit Component → Browser Rendering
```

## Scene Configuration

### Scene Parameters
```python
{
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
    "theme": "minimal",
    "lighting": "soft",
    "atmosphere": "clean"
}
```

### Cover Configuration
```python
{
    "title": "VOGUE",
    "subtitle": "Collection 2026",
    "badges": ["Total Look", "AI Styled"]
}
```

## Director Command Examples

### Basic Commands
- "Make it Paris Fashion Week style"
- "Cyberpunk Tokyo with neon lights"
- "Editorial 90s aesthetic"

### Advanced Commands
- "Camera closer and lower, dramatic lighting"
- "Add more fog, make it mysterious"
- "Red carpet style with bright spotlights"
- "Minimalist, clean, soft shadows"

### Cover Customization
- "Make the cover say 'TOKYO NIGHT'"
- "Add badges: waterproof, office-to-party"
- "90s editorial style cover"

## API Reference

### `build_runway_scene()`
Builds a complete runway scene from filtered dataset items.

```python
scene = build_runway_scene(
    items_data=items_list,
    preset="minimal",
    cover_title="VOGUE",
    cover_subtitle="Collection 2026",
    cover_badges=["Total Look"]
)
```

### `parse_director_command()`
Parses natural language director command into structured configuration.

```python
command = parse_director_command(
    command="Make it cyberpunk Tokyo",
    model="zai-glm-4.7"
)
```

### `generate_runway_html()`
Generates HTML for runway widget with scene data injected.

```python
html = generate_runway_html(scene, widget_path="ui/runway_widget.html")
```

## Performance Considerations

### Image Processing
- Images are resized to 400x400px maximum
- Converted to base64 data URIs to avoid CORS issues
- Processing happens on the backend before rendering

### Browser Rendering
- WebGL rendering uses user's GPU acceleration
- Three.js CDN loaded from reliable source
- Scene optimized for smooth 60fps animation

### LLM Calls
- Director commands use lightweight models (configured in `runway_director.py`)
- JSON-only responses for fast parsing
- Fallback to presets if parsing fails

## Troubleshooting

### Images Not Loading
- Check if image URLs are accessible
- Verify internet connection for CDN resources
- Try a different preset to reset the scene

### Scene Not Updating
- Clear browser cache
- Refresh the page
- Check browser console for JavaScript errors

### Director Commands Not Working
- Verify `API_KEY_CEREBRAS` (or `CEREBRAS_API_KEY`) is set
- Check if the model is available
- Try simpler commands first

## Future Enhancements

Potential improvements for future versions:
- [ ] Camera controls (orbit, zoom, pan)
- [ ] More transition effects (glitch, neon pulse, zoom)
- [ ] Custom particle shapes and colors
- [ ] Audio integration (music, sound effects)
- [ ] Export scene as video
- [ ] Multiple runway layouts
- [ ] Real-time collaboration

## Credits

- **Three.js** - 3D graphics library
- **Streamlit** - Web application framework
- **OpenAI** - LLM for director command parsing
- **Pillow** - Image processing
