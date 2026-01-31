<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import {
		Content,
		Grid,
		Row,
		Column,
		Tile,
		Button,
		Tag,
		InlineNotification,
		SkeletonText,
		ButtonSet
	} from 'carbon-components-svelte';
	import { ArrowLeft, DocumentDownload, Maximize } from 'carbon-icons-svelte';
	import { goto } from '$app/navigation';
	import { historyAPI } from '$lib/api';

	// Get the entry ID from the URL
	let entryId = $derived($page.params.id);

	// State
	let entry = $state<any>(null);
	let isLoading = $state(true);
	let errorMessage = $state('');
	let isFullscreen = $state(false);

	// Load entry data
	async function loadEntry() {
		if (!entryId) return;
		
		isLoading = true;
		errorMessage = '';
		
		try {
			entry = await historyAPI.getTranslation(entryId);
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to load entry';
		} finally {
			isLoading = false;
		}
	}

	// Format date
	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	// Format transcript text into readable paragraphs (same logic as backend)
	function prepareTextForDisplay(text: string): string {
		if (!text) return '';
		
		const lines = text.split('\n');
		const paragraphs: string[] = [];
		let currentPara: string[] = [];
		
		for (let line of lines) {
			line = line.trim();
			if (!line) {
				if (currentPara.length > 0) {
					paragraphs.push(currentPara.join(' '));
					currentPara = [];
				}
			} else {
				if (line && '.!?:;'.includes(line.slice(-1))) {
					currentPara.push(line);
					if (currentPara.length > 3) {
						paragraphs.push(currentPara.join(' '));
						currentPara = [];
					}
				} else {
					currentPara.push(line);
				}
			}
		}
		
		if (currentPara.length > 0) {
			paragraphs.push(currentPara.join(' '));
		}
		
		return paragraphs.join('\n\n');
	}

	// Get display text - use processed version for YouTube transcripts
	function getDisplayText(entry: any, isOriginal: boolean): string {
		if (!entry) return '';
		
		const text = isOriginal ? entry.original_text : entry.translated_text;
		if (!text) return '';
		
		// For YouTube entries, format the original text into paragraphs
		// For translated text, it should already have proper formatting
		if (isOriginal && entry.type === 'youtube') {
			return prepareTextForDisplay(text);
		}
		
		return text;
	}


	// Export content
	function exportContent() {
		if (!entry) return;
		
		const originalText = getDisplayText(entry, true);
		const translatedText = getDisplayText(entry, false);
		
		const content = `${entry.title}
${entry.type === 'youtube' ? `URL: ${entry.youtube_url}` : ''}
Source Language: ${entry.source_lang}
Target Language: ${entry.target_lang}
Provider: ${entry.provider}
Created: ${formatDate(entry.created_at)}

ORIGINAL TEXT:
${originalText}

${translatedText ? `TRANSLATED TEXT:
${translatedText}` : ''}
`;
		
		const blob = new Blob([content], { type: 'text/plain' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${entry.title.substring(0, 50).replace(/[^a-zA-Z0-9]/g, '_')}.txt`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	// Go back to history
	function goBack() {
		goto('/history');
	}

	// Fullscreen toggle
	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
		
		// Manage body class to prevent background scrolling
		if (isFullscreen) {
			document.body.classList.add('fullscreen-mode');
		} else {
			document.body.classList.remove('fullscreen-mode');
		}
	}

	// Handle escape key to exit fullscreen
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isFullscreen) {
			isFullscreen = false;
		}
	}

	// Synchronized scrolling
	let originalPanel: HTMLElement;
	let translatedPanel: HTMLElement;
	let isScrolling = $state(false);
	
	// Paragraph linking state
	let hoveredParagraphIndex = $state<number | null>(null);

	function handleScroll(event: Event, isOriginal: boolean) {
		if (isScrolling) return;
		
		const sourcePanel = event.target as HTMLElement;
		const targetPanel = isOriginal ? translatedPanel : originalPanel;
		
		if (!sourcePanel || !targetPanel) return;
		
		// Calculate scroll percentage
		const scrollTop = sourcePanel.scrollTop;
		const scrollHeight = sourcePanel.scrollHeight - sourcePanel.clientHeight;
		const scrollPercentage = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
		
		// Apply to target panel
		const targetScrollHeight = targetPanel.scrollHeight - targetPanel.clientHeight;
		const targetScrollTop = scrollPercentage * targetScrollHeight;
		
		isScrolling = true;
		targetPanel.scrollTop = targetScrollTop;
		
		// Reset flag immediately using requestAnimationFrame
		requestAnimationFrame(() => {
			isScrolling = false;
		});
	}
	
	// Handle paragraph hover
	function handleParagraphHover(index: number) {
		hoveredParagraphIndex = index;
	}
	
	function handleParagraphLeave() {
		hoveredParagraphIndex = null;
	}

	onMount(() => {
		loadEntry();
		// Add keyboard listener for escape key
		window.addEventListener('keydown', handleKeydown);
		
		return () => {
			window.removeEventListener('keydown', handleKeydown);
			// Clean up body class
			document.body.classList.remove('fullscreen-mode');
		};
	});
</script>

<svelte:head>
	<title>{entry ? `View: ${entry.title}` : 'View Translation'}</title>
</svelte:head>

<Content>
	<Grid class={isFullscreen ? 'fullscreen' : ''}>
		<!-- Header -->
		<Row>
			<Column sm={4} md={8} lg={16} xlg={16} max={15}>
				<div class="view-header">
					<Button
						kind="ghost"
						icon={ArrowLeft}
						on:click={goBack}
					>
						Back to History
					</Button>
					
					{#if entry}
						<ButtonSet>
							<Button
								kind="ghost"
								icon={Maximize}
								iconDescription="Fullscreen view"
								onclick={toggleFullscreen}
							>
								Fullscreen
							</Button>
							<Button
								kind="secondary"
								icon={DocumentDownload}
								onclick={exportContent}
							>
								Export
							</Button>
						</ButtonSet>
					{/if}
				</div>
			</Column>
		</Row>

		{#if isLoading}
			<!-- Loading state -->
			<Row>
				<Column sm={4} md={8} lg={16} xlg={16} max={15}>
					<Tile>
						<div class="skeleton-content">
							<SkeletonText heading />
							<SkeletonText paragraph lines={3} />
						</div>
					</Tile>
				</Column>
			</Row>
		{:else if errorMessage}
			<!-- Error state -->
			<Row>
				<Column sm={4} md={8} lg={16} xlg={16} max={15}>
					<InlineNotification
						kind="error"
						title="Error"
						subtitle={errorMessage}
						hideCloseButton
					/>
				</Column>
			</Row>
		{:else if entry}
			<!-- Title and metadata -->
			<Row>
				<Column sm={4} md={8} lg={16} xlg={16} max={15}>
					<Tile light>
						<h1>{entry.title}</h1>
						<div class="entry-meta">
							<Tag type={entry.type === 'youtube' ? 'purple' : 'cyan'}>
								{entry.type === 'youtube' ? 'YouTube' : 'Text'}
							</Tag>
							<Tag type="gray">{entry.source_lang} → {entry.target_lang}</Tag>
							<Tag type="gray">{entry.provider}</Tag>
							<span class="date">{formatDate(entry.created_at)}</span>
						</div>
						
						{#if entry.type === 'youtube' && entry.youtube_url}
							<div class="youtube-info">
								<a href={entry.youtube_url} target="_blank" rel="noopener">
									🔗 Open YouTube Video
								</a>
							</div>
						{/if}
					</Tile>
				</Column>
			</Row>

			<!-- Side-by-side text display -->
			<Row>
				<Column sm={4} md={4} lg={8} xlg={8} max={8}>
					<h3>Original Text ({entry.source_lang})</h3>
					<div class="char-count">{entry.original_text.length} characters</div>
					<Tile class="text-scroll-tile">
						<div 
							class="text-content" 
							bind:this={originalPanel}
							onscroll={(e) => handleScroll(e, true)}
						>
							{#each getDisplayText(entry, true).split('\n\n') as paragraph, index}
								{#if paragraph.trim()}
									<p 
										data-paragraph-index={index}
										class="paragraph"
										class:highlighted={hoveredParagraphIndex === index}
										onmouseenter={() => handleParagraphHover(index)}
										onmouseleave={handleParagraphLeave}
									>
										{paragraph}
									</p>
								{/if}
							{/each}
						</div>
					</Tile>
				</Column>
				
				<Column sm={4} md={4} lg={8} xlg={8} max={8}>
					<h3>Translated Text ({entry.target_lang})</h3>
					<div class="char-count">
						{entry.translated_text ? entry.translated_text.length : 0} characters
					</div>
					<Tile class="text-scroll-tile">
						<div 
							class="text-content" 
							bind:this={translatedPanel}
							onscroll={(e) => handleScroll(e, false)}
						>
							{#if entry.translated_text}
								{#each getDisplayText(entry, false).split('\n\n') as paragraph, index}
									{#if paragraph.trim()}
										<p 
											data-paragraph-index={index}
											class="paragraph"
											class:highlighted={hoveredParagraphIndex === index}
											onmouseenter={() => handleParagraphHover(index)}
											onmouseleave={handleParagraphLeave}
										>
											{paragraph}
										</p>
									{/if}
								{/each}
							{:else}
								<p class="placeholder">No translation available</p>
							{/if}
						</div>
					</Tile>
				</Column>
			</Row>
		{:else}
			<Row>
				<Column sm={4} md={8} lg={16} xlg={16} max={15}>
					<InlineNotification
						kind="warning"
						title="Not Found"
						subtitle="The requested entry could not be found"
						hideCloseButton
					/>
				</Column>
			</Row>
		{/if}
	</Grid>
</Content>

<!-- Fullscreen Exit Button (only visible in fullscreen) -->
{#if isFullscreen}
	<button class="fullscreen-exit-btn" onclick={toggleFullscreen} title="Exit fullscreen (Esc)">
		✕
	</button>
{/if}

<style>
	/* MINIMAL CUSTOM CSS - Only what Carbon doesn't provide */
	
	/* 1. Fullscreen mode - app-specific feature not in Carbon */
	:global(body.fullscreen-mode) {
		overflow: hidden;
	}

	:global(body.fullscreen-mode .bx--header) {
		display: none;
	}

	:global(.fullscreen) {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		/* Background will be inherited from active Carbon theme */
		z-index: 9999;
		padding: 0 !important;
		max-width: none !important;
		display: flex;
		justify-content: center;
		align-items: flex-start;
	}
	
	:global(.fullscreen > .bx--grid) {
		width: 100%;
		max-width: 1920px; /* Reasonable max for readability */
		margin: 0 auto;
	}

	/* Hide non-essential elements in fullscreen */
	:global(.fullscreen) :global(.bx--row) {
		margin: 0;
	}

	:global(.fullscreen) .view-header {
		display: none;
	}

	:global(.fullscreen) :global(.bx--row:first-of-type) {
		display: none;
	}

	:global(.fullscreen) :global(.bx--tile) {
		display: none;
	}

	:global(.fullscreen) :global(.bx--tile.text-scroll-tile) {
		display: block;
		height: 100vh !important;
		border-radius: 0;
		border: none;
	}
	
	/* Make columns use full available width in fullscreen */
	:global(.fullscreen) :global(.bx--col-lg-7),
	:global(.fullscreen) :global(.bx--col-xlg-7),
	:global(.fullscreen) :global(.bx--col-max-7) {
		flex: 1;
		max-width: 50%;
	}

	:global(.fullscreen) h3 {
		position: sticky;
		top: 0;
		/* Background and colors inherited from active theme */
		margin: 0;
		padding: 16px;
		z-index: 1;
	}

	:global(.fullscreen) .char-count {
		display: none;
	}

	:global(.fullscreen) .text-content {
		padding: 32px;
		font-size: 1rem;
		height: calc(100vh - 60px);
		padding-top: 80px;
	}

	:global(.fullscreen) .paragraph {
		padding-left: 40px;
		margin-bottom: 32px;
	}

	:global(.fullscreen) .paragraph[data-paragraph-index]::before {
		left: 16px;
	}

	.fullscreen-exit-btn {
		position: fixed;
		top: 16px;
		right: 16px;
		/* Use Carbon button-like styling that follows theme */
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		font-size: 1.25rem;
		cursor: pointer;
		padding: 8px;
		border-radius: 4px;
		width: 2.5rem;
		height: 2.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		line-height: 1;
		z-index: 10001;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
		backdrop-filter: blur(8px);
	}

	.fullscreen-exit-btn:hover {
		background: rgba(255, 255, 255, 0.2);
		transform: scale(1.05);
	}

	/* 2. Scrollable text area - app-specific */
	:global(.text-scroll-tile) {
		height: 600px;
		overflow-y: auto;
	}
	
	.text-content {
		height: 100%;
		overflow-y: auto;
		font-size: 0.875rem;
		line-height: 1.6;
	}
	
	.text-content p {
		margin-bottom: 24px;
		line-height: 1.6;
	}
	
	.text-content p:last-child {
		margin-bottom: 0;
	}
	
	/* 3. Paragraph linking - app-specific feature */
	:global(.paragraph) {
		padding: 12px 16px 16px 40px;
		margin-bottom: 32px !important;
		border-left: 3px solid transparent;
		cursor: pointer;
		position: relative;
		display: block;
		transition: background-color 0.2s ease;
	}
	
	:global(.paragraph:hover) {
		background-color: rgba(0, 0, 0, 0.05);
		border-left-color: #0f62fe;
	}
	
	:global(.paragraph.highlighted) {
		background-color: rgba(15, 98, 254, 0.1);
		border-left-color: #0f62fe;
	}
	
	/* Paragraph numbers on hover */
	:global(.paragraph[data-paragraph-index]::before) {
		content: attr(data-paragraph-index);
		position: absolute;
		left: 16px;
		top: 12px;
		font-size: 0.75rem;
		color: #8d8d8d;
		opacity: 0;
		transition: opacity 0.2s ease;
	}
	
	:global(.paragraph:hover::before),
	:global(.paragraph.highlighted::before) {
		opacity: 1;
	}

	
	/* 4. Helper classes for layout */
	.view-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 32px;
		gap: 16px;
		flex-wrap: wrap;
	}
	
	/* Prevent ButtonSet from causing overflow */
	.view-header :global(.bx--btn-set) {
		flex-shrink: 0;
		flex-wrap: wrap;
		gap: 8px;
	}
	
	.skeleton-content {
		padding: 32px;
	}
	
	h1 {
		font-size: 1.5rem;
		font-weight: 600;
		margin-bottom: 16px;
		line-height: 1.4;
	}
	
	.entry-meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 12px;
		margin-bottom: 16px;
	}
	
	.date {
		font-size: 0.875rem;
		color: #525252;
	}
	
	.youtube-info {
		margin-bottom: 16px;
	}
	
	.youtube-info a {
		color: #0f62fe;
		text-decoration: none;
		font-size: 0.875rem;
	}
	
	.youtube-info a:hover {
		text-decoration: underline;
	}
	
	h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 8px;
	}
	
	.char-count {
		font-size: 0.75rem;
		color: #525252;
		margin-bottom: 16px;
	}
	
	.placeholder {
		color: #8d8d8d;
		font-style: italic;
		text-align: center;
		padding: 32px;
	}
	
	/* 5. Mobile adjustments */
	@media (max-width: 768px) {
		:global(.text-scroll-tile) {
			height: 300px;
		}
		
		.view-header {
			flex-direction: column;
			align-items: stretch;
			gap: 16px;
		}
		
		.view-header :global(.bx--btn-set) {
			display: flex;
			flex-direction: column;
			width: 100%;
		}
		
		.view-header :global(.bx--btn-set .bx--btn) {
			width: 100%;
			justify-content: center;
		}
		
		.entry-meta {
			flex-direction: column;
			align-items: flex-start;
		}
	}
</style>