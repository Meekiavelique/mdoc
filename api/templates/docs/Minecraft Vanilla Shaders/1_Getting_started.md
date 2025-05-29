# Introduction to Minecraft Core Shaders

This documentation contains a complete crash course in Minecraft core shader programming. 

This page contains the very basic overview of what shaders are, how they work in Minecraft, and everything you need to get started writing your first vanilla shader modifications.

We'll walk you through understanding the rendering pipeline, and writing your first shader.

For those of you who are already familiar with basic shader concepts, go ahead and use the navigation to jump to what you're interested in. If you're interested in contributing examples or improvements, feel free to do it!

```hint info
These tutorials are for Minecraft Java Edition 1.21.4+ and focus specifically on core shaders available through resource packs. This documentation does not cover OptiFine shaders, which are a completely different system.
```

## What Are Shaders?

Think of shaders as tiny programs that run on your graphics card. Every single pixel you see on your screen when playing Minecraft goes through these programs. There are two main types:

**Vertex Shaders**: These process the corners (vertices) of 3D shapes. They decide where things appear on your screen.

**Fragment Shaders**: These decide what color each pixel should be. They handle textures, lighting, and special effects.

When you see a blue sky in Minecraft, that's a shader painting each pixel blue. When you see water reflecting light, that's a shader calculating how light bounces off the surface. Everything visual goes through shaders.

## Prerequisites

You don't need to be a programmer to start with shaders, but some basic concepts help:

- **Basic math**: Understanding coordinates (x, y, z) and simple operations
- **GLSL**: You need to learn GLSL before starting with core shaders

## Development Environment

To write shaders effectively, you'll need:

- **Minecraft Java Edition 1.21.4+**: Required for core shader support
- **Text Editor**: Something that can highlight GLSL syntax (VS Code, Sublime Text, etc.)
- **Shader Reload Mod (Optional)**: Essential tool that lets you reload shaders without restarting Minecraft
  - Download: [https://modrinth.com/mod/shader-reload](https://modrinth.com/mod/shader-reload)

## Community and Resources

The Minecraft shader community is very helpful :)

### Discord Communities
- **ShaderLabs**: [https://discord.gg/nGFnwBbTDN](https://discord.gg/nGFnwBbTDN)
- **Minecraft Commands**: [https://discord.gg/QAFXFtZ](https://discord.gg/QAFXFtZ)
- **Crowdford Community**: [https://discord.gg/SnrGDJKmWj](https://discord.gg/SnrGDJKmWj)
- **Godlands**: [https://discord.gg/2XyCvD6y7U](https://discord.gg/2XyCvD6y7U)
- **Meek Basement**: [https://discord.gg/avSH2JTfef](https://discord.gg/avSH2JTfef)

### Learning Resources
- **GitHub repositories**: [[Minecraft Vanilla Shaders/resources]]
- **YouTube tutorials**: [Vanilla shaders](https://www.youtube.com/watch?v=QriexCR0YYg&list=PLTRX9BDGoc4flt8c1t0UrqzyaVZw_F5eP)

