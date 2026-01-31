<script lang="ts">
	// Import all Carbon themes
	import "carbon-components-svelte/css/all.css";

	import { onMount } from 'svelte';
	import {
		Header,
		SideNav,
		SideNavItems,
		SideNavLink,
		SkipToContent,
		Theme
	} from "carbon-components-svelte";
	
	// Icons for rail navigation
	import Language from "carbon-icons-svelte/lib/Language.svelte";
	import RecentlyViewed from "carbon-icons-svelte/lib/RecentlyViewed.svelte";
	import Settings from "carbon-icons-svelte/lib/Settings.svelte";

	import favicon from '$lib/assets/favicon.svg';
	import { loadSettings, settings } from '$lib/stores/settings.js';

	let { children } = $props();
	
	// Rail navigation state - starts collapsed on mobile, open on desktop
	let isSideNavOpen = $state(false);
	let innerWidth = $state(0);
	
	// Load settings on app initialization
	onMount(async () => {
		await loadSettings();
	});
	
	// Theme reactive variable for Carbon Theme component
	let currentTheme = $state('white');
	
	// Sync theme with settings when settings change
	$effect(() => {
		if ($settings.theme) {
			currentTheme = $settings.theme;
		}
	});
	
	// Update settings when theme changes via Theme component
	$effect(() => {
		if (currentTheme !== $settings.theme && currentTheme) {
			// This allows the Theme component to update settings
			settings.update(s => ({ ...s, theme: currentTheme }));
		}
	});
	
	// Auto-open rail on desktop for better UX
	$effect(() => {
		if (innerWidth >= 1056) {
			isSideNavOpen = true;
		}
	});
</script>

<svelte:window bind:innerWidth />

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<Theme bind:theme={currentTheme} persist persistKey="ytt-theme">
	<Header company="YTT" platformName="YouTube Transcript Translator" bind:isSideNavOpen>
		<!-- No HeaderNav items - using rail SideNav instead -->
	</Header>

	<SideNav bind:isOpen={isSideNavOpen} rail>
		<SideNavItems>
			<SideNavLink 
				href="/" 
				text="Translator" 
				icon={Language}
			/>
			<SideNavLink 
				href="/history" 
				text="History" 
				icon={RecentlyViewed}
			/>
			<SideNavLink 
				href="/settings" 
				text="Settings" 
				icon={Settings}
			/>
		</SideNavItems>
	</SideNav>

	<SkipToContent />

	<main class="main-content">
		{@render children()}
	</main>
</Theme>

<style>
	.main-content {
		margin-top: 48px; /* Height of Carbon header */
		padding-left: 48px; /* Width of rail nav when collapsed */
		min-height: calc(100vh - 48px);
	}
	
	/* When rail nav is expanded */
	:global(.bx--side-nav--expanded) ~ .main-content {
		padding-left: 256px; /* Width of expanded rail nav */
	}
	
	/* Mobile adjustments */
	@media (max-width: 1055px) {
		.main-content {
			padding-left: 0;
		}
	}
	
	/* SideNav theme fix - Carbon v0.99.1 doesn't properly theme SideNav */
	:global([theme="g90"]) :global(.bx--side-nav),
	:global([theme="g100"]) :global(.bx--side-nav) {
		background-color: #262626;
		color: #f4f4f4;
	}
	
	:global([theme="g80"]) :global(.bx--side-nav) {
		background-color: #393939;
		color: #f4f4f4;
	}
	
	:global([theme="white"]) :global(.bx--side-nav),
	:global([theme="g10"]) :global(.bx--side-nav) {
		background-color: #f4f4f4;
		color: #161616;
	}
	
	/* SideNav items theme fix */
	:global([theme="g90"]) :global(.bx--side-nav__link),
	:global([theme="g100"]) :global(.bx--side-nav__link),
	:global([theme="g80"]) :global(.bx--side-nav__link) {
		color: #f4f4f4;
	}
	
	:global([theme="g90"]) :global(.bx--side-nav__link:hover),
	:global([theme="g100"]) :global(.bx--side-nav__link:hover),
	:global([theme="g80"]) :global(.bx--side-nav__link:hover) {
		background-color: #353535;
	}
	
	:global([theme="white"]) :global(.bx--side-nav__link:hover),
	:global([theme="g10"]) :global(.bx--side-nav__link:hover) {
		background-color: #e5e5e5;
	}
</style>
