import typography from '@tailwindcss/typography';
import containerQuries from '@tailwindcss/container-queries';

/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				gray: {
					50: 'var(--color-gray-50, #f9f9f9)',
					100: 'var(--color-gray-100, #ececec)',
					200: 'var(--color-gray-200, #e3e3e3)',
					300: 'var(--color-gray-300, #cdcdcd)',
					400: 'var(--color-gray-400, #b4b4b4)',
					500: 'var(--color-gray-500, #9b9b9b)',
					600: 'var(--color-gray-600, #676767)',
					700: 'var(--color-gray-700, #4e4e4e)',
					800: 'var(--color-gray-800, #333)',
					850: 'var(--color-gray-850, #262626)',
					900: 'var(--color-gray-900, #171717)',
					950: 'var(--color-gray-950, #0d0d0d)'
				}
				// gray: {
				// 	"50": "var(--color-gray-50, #ffffff)",   // Pure White
				// 	"100": "var(--color-gray-100, #cce6e6)", // Very Light Teal (White + 20% of #008080)
				// 	"200": "var(--color-gray-200, #99cccc)", // Light Teal (White + 40% of #008080)
				// 	"300": "var(--color-gray-300, #66b3b3)", // Medium-Light Teal (White + 60% of #008080)
				// 	"400": "var(--color-gray-400, #339999)", // Tealish (White + 80% of #008080)
				// 	"500": "var(--color-gray-500, #008080)", // Pure Teal #008080
				// 	"600": "var(--color-gray-600, #036969)", // Darkening Teal (80% #008080 + 20% #0d0d0d influence)
				// 	"700": "var(--color-gray-700, #055252)", // Darker Teal (60% #008080 + 40% #0d0d0d influence)
				// 	"800": "var(--color-gray-800, #083B3B)", // Very Dark Teal (40% #008080 + 60% #0d0d0d influence)
				// 	"850": "var(--color-gray-850, #0A2C2C)", // Deepest Teal/Gray (closer to #0d0d0d)
				// 	"900": "var(--color-gray-900, #171717)", // Almost Dark Gray, hint of teal
				// 	"950": "var(--color-gray-950, #0d0d0d)"   // Target Darkest Color
				// }
			},
			typography: {
				DEFAULT: {
					css: {
						pre: false,
						code: false,
						'pre code': false,
						'code::before': false,
						'code::after': false
					}
				}
			},
			padding: {
				'safe-bottom': 'env(safe-area-inset-bottom)'
			}
		}
	},
	plugins: [typography, containerQuries]
};
