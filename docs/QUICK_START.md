# AI Runway Director - Quick Start Guide

## Installation

1. Install the new dependencies:
```bash
pip install requests Pillow
```

Or update all dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Basic Workflow

### 1. Generate a Look
- Go to the **Look Generator** tab
- Enter your fashion brief (e.g., "Summer casual outfit for a beach party")
- Click "Сгенерировать лук"
- Review the two generated looks

### 2. Send to Runway
- Select your preferred look (Look 1 or Look 2)
- Click **"🎬 Показать на подиуме"** button
- The selected items will be saved

### 3. Customize the Scene
- Switch to the **Runway Director** tab
- Choose a preset from the dropdown:
  - **Paris Runway** - Elegant, warm lighting
  - **Cyberpunk Tokyo** - Neon, futuristic
  - **Editorial 90s** - Clean, high contrast
  - **Red Carpet** - Dramatic, glamorous
  - **Minimal** - Clean, soft lighting

### 4. Use Director Commands (Optional)
Enter natural language commands like:
- "Make it like Paris Fashion Week"
- "Cyberpunk Tokyo with neon lights"
- "Camera closer and lower"
- "Add more fog, make it mysterious"

Click **"🎬 Применить команду"** to apply changes.

### 5. Enjoy the Show
- Watch your items displayed on the 3D runway
- See animated particles and lighting effects
- View the Vogue-style cover overlay

## Example Director Commands

### Scene Styling
```
"Make it Paris Fashion Week style, minimalism, soft light"
"Now cyberpunk Tokyo, rain, neon, camera closer"
"Editorial 90s aesthetic with white background"
"Red carpet style with bright spotlights"
```

### Camera Control
```
"Camera closer and lower"
"Zoom out, show the whole runway"
"Camera from above, bird's eye view"
```

### Atmosphere
```
"Add more fog, make it mysterious"
"Clean and bright atmosphere"
"Dramatic shadows, moody lighting"
```

### Cover Customization
```
"Make the cover say 'TOKYO NIGHT'"
"Add badges: waterproof, office-to-party"
"90s editorial style cover with large font"
```

## Troubleshooting

### Images Not Loading
- Check your internet connection
- Verify image URLs are accessible
- Try refreshing the page

### Scene Not Updating
- Clear browser cache
- Refresh the page
- Check browser console for errors

### Director Commands Not Working
- Verify OPENAI_API_KEY is set in `.env` file
- Try simpler commands first
- Check if the selected model is available

## Tips for Best Results

1. **Start with presets** - Choose a preset first, then fine-tune with commands
2. **Be specific** - More detailed commands give better results
3. **Experiment** - Try different combinations of presets and commands
4. **Use examples** - Reference the example commands for inspiration

## Keyboard Shortcuts

- `Ctrl + Enter` - Generate look (when in text area)
- `Alt + 1` - Switch to Look Generator tab
- `Alt + 2` - Switch to Runway Director tab

## Performance Tips

- Images are automatically resized to 400x400px
- Use lightweight models (gpt-4.1-mini) for director commands
- Close other browser tabs for better performance

## Getting Help

- Check the full documentation: `docs/RUNWAY_MODE.md`
- Review the code comments in `runway_director.py`
- Check Streamlit logs for errors

## Next Steps

- Try all 5 presets to see different styles
- Experiment with complex director commands
- Create your own custom presets by modifying `runway_director.py`
- Share your runway presentations with others!