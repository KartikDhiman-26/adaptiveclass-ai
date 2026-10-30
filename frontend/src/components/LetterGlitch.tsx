import React, { useRef, useEffect } from 'react';

export interface LetterGlitchProps {
  glitchSpeed?: number;
  centerVignette?: boolean;
  outerVignette?: boolean;
  smooth?: boolean;
  characters?: string;
  className?: string;
}

interface LetterItem {
  char: string;
  color: string;
  targetColor: string;
  colorProgress: number;
  brightness: number;
  isHighlight: boolean;
}

// Utility: convert 3 or 6-character hex to RGB values
const hexToRgb = (hex: string): { r: number; g: number; b: number } => {
  let cleaned = hex.replace('#', '');
  if (cleaned.length === 3) {
    cleaned = cleaned.split('').map(c => c + c).join('');
  }
  const num = parseInt(cleaned, 16);
  if (isNaN(num)) return { r: 50, g: 50, b: 50 };
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  };
};

// Utility: linear interpolation between colors
const interpolateRgb = (
  c1: { r: number; g: number; b: number },
  c2: { r: number; g: number; b: number },
  factor: number
): string => {
  const r = Math.round(c1.r + factor * (c2.r - c1.r));
  const g = Math.round(c1.g + factor * (c2.g - c1.g));
  const b = Math.round(c1.b + factor * (c2.b - c1.b));
  return `rgb(${r}, ${g}, ${b})`;
};

const DEFAULT_CHARS = '01ABCDEFGHIJKLMNOPQRSTUVWXYZ{}[]<>/+-=*~#@λΣπ';

// Palette pools:
// 60% neutral gray tones, 28% subdued forest green, 12% selective crimson-red highlights
const NEUTRAL_GRAYS = ['#3E3E3E', '#52504E', '#6E6A66', '#898582', '#B7B3B0'];
const FOREST_GREENS = ['#152B20', '#1C3B2B', '#264E3A', '#32654B'];
const CRIMSON_ACCENTS = ['#A31C1B', '#C12A29', '#E24A49'];

const getWeightedRandomColor = (): { color: string; isHighlight: boolean; brightness: number } => {
  const roll = Math.random();
  if (roll < 0.60) {
    // Neutral Grays: medium to high depth
    const color = NEUTRAL_GRAYS[Math.floor(Math.random() * NEUTRAL_GRAYS.length)];
    const brightness = 0.50 + Math.random() * 0.35; // 0.50 - 0.85
    return { color, isHighlight: false, brightness };
  } else if (roll < 0.88) {
    // Subdued Forest Green: creates technical intelligence ambiance
    const color = FOREST_GREENS[Math.floor(Math.random() * FOREST_GREENS.length)];
    const brightness = 0.55 + Math.random() * 0.35; // 0.55 - 0.90
    return { color, isHighlight: false, brightness };
  } else {
    // Selective Crimson Highlights: vibrant accent depth
    const color = CRIMSON_ACCENTS[Math.floor(Math.random() * CRIMSON_ACCENTS.length)];
    const brightness = 0.85 + Math.random() * 0.15; // 0.85 - 1.00
    return { color, isHighlight: true, brightness };
  }
};

export const LetterGlitch: React.FC<LetterGlitchProps> = ({
  glitchSpeed = 55,
  centerVignette = true,
  outerVignette = true,
  smooth = true,
  characters = DEFAULT_CHARS,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const lettersRef = useRef<LetterItem[]>([]);
  const gridRef = useRef<{ columns: number; rows: number }>({ columns: 0, rows: 0 });
  const lastUpdateRef = useRef<number>(0);
  const isVisibleRef = useRef<boolean>(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Check user's preferred motion setting
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const getRandomChar = () => characters[Math.floor(Math.random() * characters.length)];

    // Setup canvas size matching container client dimensions
    const setupCanvas = () => {
      if (!canvas || !container) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = container.clientWidth;
      const height = container.clientHeight;

      if (width === 0 || height === 0) return;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.scale(dpr, dpr);

      const charWidth = 14;
      const charHeight = 18;
      const columns = Math.ceil(width / charWidth);
      const rows = Math.ceil(height / charHeight);

      gridRef.current = { columns, rows };
      const totalLetters = columns * rows;

      lettersRef.current = Array.from({ length: totalLetters }, () => {
        const item = getWeightedRandomColor();
        const target = getWeightedRandomColor();
        return {
          char: getRandomChar(),
          color: item.color,
          targetColor: target.color,
          colorProgress: 1.0,
          brightness: item.brightness,
          isHighlight: item.isHighlight
        };
      });

      // Initial single paint
      renderFrame(ctx, width, height, columns, charWidth, charHeight);
    };

    // Render single frame on canvas with dynamic brightness and depth
    const renderFrame = (
      context: CanvasRenderingContext2D,
      width: number,
      height: number,
      columns: number,
      charWidth: number,
      charHeight: number
    ) => {
      context.clearRect(0, 0, width, height);
      context.font = '11px "JetBrains Mono", ui-monospace, SFMono-Regular, monospace';
      context.textBaseline = 'top';

      const letters = lettersRef.current;
      for (let i = 0; i < letters.length; i++) {
        const letter = letters[i];
        const x = (i % columns) * charWidth;
        const y = Math.floor(i / columns) * charHeight;

        context.globalAlpha = letter.brightness;
        context.fillStyle = letter.color;
        context.fillText(letter.char, x, y);
      }
      context.globalAlpha = 1.0;
    };

    // Continuous animation loop
    const animate = (timestamp: number) => {
      if (!isVisibleRef.current || prefersReducedMotion) {
        return;
      }

      if (timestamp - lastUpdateRef.current >= glitchSpeed) {
        lastUpdateRef.current = timestamp;

        const letters = lettersRef.current;
        const total = letters.length;
        // Scramble a subset of characters per tick (8% of grid)
        const scrambleCount = Math.max(4, Math.floor(total * 0.08));

        for (let s = 0; s < scrambleCount; s++) {
          const idx = Math.floor(Math.random() * total);
          const item = letters[idx];
          if (item) {
            item.char = getRandomChar();
            const next = getWeightedRandomColor();
            item.isHighlight = next.isHighlight;
            item.brightness = next.brightness;
            if (smooth) {
              item.targetColor = next.color;
              item.colorProgress = 0;
            } else {
              item.color = next.color;
            }
          }
        }

        // Smooth transition step
        if (smooth) {
          for (let i = 0; i < total; i++) {
            const item = letters[i];
            if (item.colorProgress < 1.0) {
              item.colorProgress = Math.min(1.0, item.colorProgress + 0.16);
              const c1 = hexToRgb(item.color);
              const c2 = hexToRgb(item.targetColor);
              item.color = interpolateRgb(c1, c2, item.colorProgress);
            }
          }
        }

        const width = container.clientWidth;
        const height = container.clientHeight;
        const { columns } = gridRef.current;
        renderFrame(ctx, width, height, columns, 14, 18);
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    setupCanvas();

    if (!prefersReducedMotion) {
      animationFrameRef.current = requestAnimationFrame(animate);
    }

    // ResizeObserver for container resizing
    const resizeObserver = new ResizeObserver(() => {
      setupCanvas();
    });
    resizeObserver.observe(container);

    // IntersectionObserver to pause rendering when out of viewport
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          isVisibleRef.current = entry.isIntersecting;
          if (entry.isIntersecting && !prefersReducedMotion) {
            if (!animationFrameRef.current) {
              animationFrameRef.current = requestAnimationFrame(animate);
            }
          } else {
            if (animationFrameRef.current) {
              cancelAnimationFrame(animationFrameRef.current);
              animationFrameRef.current = null;
            }
          }
        });
      },
      { threshold: 0.05 }
    );
    intersectionObserver.observe(container);

    // Visibility change (pause when tab is inactive)
    const handleVisibilityChange = () => {
      isVisibleRef.current = document.visibilityState === 'visible';
      if (document.visibilityState === 'visible' && !prefersReducedMotion) {
        if (!animationFrameRef.current) {
          animationFrameRef.current = requestAnimationFrame(animate);
        }
      } else {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [glitchSpeed, smooth, characters]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full overflow-hidden pointer-events-none select-none ${className}`}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="block w-full h-full opacity-85" />

      {/* Radial Center Vignette - Keeps center readable with charcoal transparency */}
      {centerVignette && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'radial-gradient(ellipse at center, rgba(23, 23, 23, 0.78) 0%, rgba(23, 23, 23, 0.58) 55%, rgba(6, 17, 12, 0.35) 100%)'
          }}
        />
      )}

      {/* Outer Edge Vignette - Blends canvas into charcoal #171717 background */}
      {outerVignette && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'linear-gradient(to bottom, rgba(23, 23, 23, 1) 0%, rgba(23, 23, 23, 0) 15%, rgba(23, 23, 23, 0) 85%, rgba(23, 23, 23, 1) 100%), linear-gradient(to right, rgba(23, 23, 23, 1) 0%, rgba(23, 23, 23, 0) 10%, rgba(23, 23, 23, 0) 90%, rgba(23, 23, 23, 1) 100%)'
          }}
        />
      )}
    </div>
  );
};
