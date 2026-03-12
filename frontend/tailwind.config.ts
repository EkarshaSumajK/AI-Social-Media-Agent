import type { Config } from 'tailwindcss';
import tailwindcssAnimate from 'tailwindcss-animate';

const config: Config = {
	content: [
		'./app/**/*.{js,ts,jsx,tsx,mdx}',
		'./components/**/*.{js,ts,jsx,tsx,mdx}',
		'./lib/**/*.{js,ts,jsx,tsx,mdx}',
	],
	// Class-based dark mode so `.dark` class on <html> activates Tailwind dark: variants
	darkMode: ['class', 'class'],
	theme: {
		extend: {
			colors: {
				canvas: 'rgb(var(--rgb-canvas)    / <alpha-value>)',
				surface: 'rgb(var(--rgb-surface)   / <alpha-value>)',
				'surface-2': 'rgb(var(--rgb-surface-2) / <alpha-value>)',
				'surface-3': 'rgb(var(--rgb-surface-3) / <alpha-value>)',
				ink: 'rgb(var(--rgb-ink)       / <alpha-value>)',
				'ink-soft': 'rgb(var(--rgb-ink-soft)  / <alpha-value>)',
				'ink-faint': 'rgb(var(--rgb-ink-faint) / <alpha-value>)',
				mist: 'rgb(var(--rgb-surface-2) / <alpha-value>)',
				'apple-blue': {
					DEFAULT: '#007AFF',
					dim: 'rgba(0,122,255,0.12)',
					glow: 'rgba(0,122,255,0.2)'
				},
				horizon: {
					DEFAULT: '#06b6d4',
					dim: 'rgba(6,182,212,0.12)'
				},
				connect: {
					DEFAULT: '#8b5cf6',
					dim: 'rgba(139,92,246,0.12)'
				},
				parentshala: {
					DEFAULT: '#ec4899',
					dim: 'rgba(236,72,153,0.12)'
				},
				success: '#22c55e',
				warning: '#f59e0b',
				danger: '#ef4444',
				info: '#3b82f6',
				ocean: '#3b82f6',
				ember: '#ef4444',
				moss: '#22c55e',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				chart: {
					'1': 'hsl(var(--chart-1))',
					'2': 'hsl(var(--chart-2))',
					'3': 'hsl(var(--chart-3))',
					'4': 'hsl(var(--chart-4))',
					'5': 'hsl(var(--chart-5))'
				},
				sidebar: {
					DEFAULT: 'hsl(var(--sidebar-background))',
					foreground: 'hsl(var(--sidebar-foreground))',
					primary: 'hsl(var(--sidebar-primary))',
					'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
					accent: 'hsl(var(--sidebar-accent))',
					'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
					border: 'hsl(var(--sidebar-border))',
					ring: 'hsl(var(--sidebar-ring))'
				}
			},
			fontFamily: {
				sans: ['var(--font-sans)'],
				display: ['var(--font-display)'],
				mono: ['var(--font-mono)']
			},
			fontSize: {
				'2xs': [
					'0.625rem',
					{
						lineHeight: '1rem'
					}
				]
			},
			borderRadius: {
				'4xl': '2rem',
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			boxShadow: {
				'apple-sm': '0 1px 2px rgba(0, 0, 0, 0.04), 0 2px 8px rgba(0, 0, 0, 0.04)',
				'apple-md': '0 2px 4px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.08)',
				'apple-lg': '0 4px 8px rgba(0, 0, 0, 0.04), 0 12px 32px rgba(0, 0, 0, 0.12)',
				'glass-inset': 'inset 0 1px 1px rgba(255,255,255,0.15), inset 0 0 0 1px rgba(255,255,255,0.05)',
				'card-strong': '0 0 0 1px rgba(255,255,255,0.08), 0 12px 40px rgba(0,0,0,0.5)',
				'glow-amber': '0 0 20px rgba(34,197,94,0.2)',
				'glow-blue': '0 0 20px rgba(59,130,246,0.2)',
				'inset-top': 'inset 0 1px 0 rgba(255,255,255,0.06)',
				'card-light': '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.05)'
			},
			transitionTimingFunction: {
				'apple-ease': 'cubic-bezier(0.25, 0.1, 0.25, 1)',
				'apple-spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
			},
			keyframes: {
				'fade-up': {
					from: {
						opacity: '0',
						transform: 'translateY(8px)'
					},
					to: {
						opacity: '1',
						transform: 'translateY(0)'
					}
				},
				'fade-in': {
					from: {
						opacity: '0'
					},
					to: {
						opacity: '1'
					}
				},
				'pulse-dot': {
					'0%, 100%': {
						opacity: '1'
					},
					'50%': {
						opacity: '0.4'
					}
				},
				shimmer: {
					from: {
						backgroundPosition: '-200% 0'
					},
					to: {
						backgroundPosition: '200% 0'
					}
				},
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				}
			},
			animation: {
				'fade-up': 'fade-up 0.3s ease both',
				'fade-in': 'fade-in 0.2s ease both',
				'pulse-dot': 'pulse-dot 2s ease-in-out infinite',
				shimmer: 'shimmer 2s linear infinite',
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out'
			}
		}
	},
	plugins: [tailwindcssAnimate],
};

export default config;
