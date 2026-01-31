import adapter from '@sveltejs/adapter-static';
import { optimizeImports, optimizeCss } from 'carbon-preprocess-svelte';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		// Static adapter for building to static files (for bundled Docker deployment)
		adapter: adapter({
			// Output to build directory (will be copied to backend/static for FastAPI)
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',  // SPA fallback
			precompress: false,
			strict: true
		}),
		// Configure for API calls to backend
		// In dev, we'll proxy to localhost:8000
		// In production, API calls go to same origin
		alias: {
			$api: './src/lib/api'
		},
		// Ensure proper paths for production
		paths: {
			base: '',
			assets: ''
		}
	},
	preprocess: [
		vitePreprocess(),
		optimizeImports()   // Tree-shakes unused Carbon components
		// optimizeCss()    // Temporarily disabled - might be removing CSS variables
	]
};

export default config;
