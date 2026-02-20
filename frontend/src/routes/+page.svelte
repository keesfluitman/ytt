<script lang="ts">
	import {
		Content,
		Grid,
		Row,
		Column,
		Tabs,
		Tab,
		TabContent,
		TextArea,
		TextInput,
		FileUploader,
		FileUploaderDropContainer,
		FileUploaderItem,
		Select,
		SelectItem,
		Button,
		InlineLoading,
		Tile,
		InlineNotification,
		Toggle,
		Modal
	} from "carbon-components-svelte";
	
	import {
		Translate,
		DocumentDownload,
		LogoYoutube,
		Document,
		TextAlignJustify,
		View,
		Copy,
		Checkmark
	} from "carbon-icons-svelte";

	import { youtubeAPI, translationAPI } from "$lib/api";
	import type { YouTubeResponse } from "$lib/api";
	import { copyToClipboard, formatBothTexts } from "$lib/utils/clipboard";
	import { onMount } from "svelte";

	// State
	let activeTab = 0;
	let youtubeUrl = "";
	let textInput = "";
	let files = [];
	let sourceLang = "auto";
	let targetLang = "en";
	let isLoading = false;
	let isFetching = false;
	let errorMessage = "";
	let isEditMode = false;  // Track if we're in edit mode
	
	// Display state
	let originalText = "";
	let translatedText = "";
	let videoInfo: YouTubeResponse | null = null;
	let showRawTranscript = false;
	
	// Language options (will be fetched from API later)
	const languages = [
		{ id: "auto", text: "Auto-detect" },
		{ id: "en", text: "English" },
		{ id: "de", text: "German" },
		{ id: "fr", text: "French" },
		{ id: "es", text: "Spanish" },
		{ id: "it", text: "Italian" },
		{ id: "nl", text: "Dutch" },
		{ id: "pt", text: "Portuguese" },
		{ id: "ru", text: "Russian" },
		{ id: "zh", text: "Chinese" },
		{ id: "ja", text: "Japanese" }
	];

	// Load data from sessionStorage if editing
	onMount(() => {
		const editData = sessionStorage.getItem('editTranslation');
		if (editData) {
			try {
				const translation = JSON.parse(editData);
				
				// Populate fields with the translation data
				originalText = translation.original_text || "";
				translatedText = translation.translated_text || "";
				sourceLang = translation.source_lang || "auto";
				targetLang = translation.target_lang || "en";
				isEditMode = true;  // Set edit mode flag
				
				// If it's a YouTube video, populate URL and video info
				if (translation.youtube_url) {
					youtubeUrl = translation.youtube_url;
					videoInfo = {
						video_id: translation.video_id,
						title: translation.title,
						url: translation.youtube_url,
						video_info: translation.video_info || {},
						available_languages: translation.available_languages || [],
						source_lang: translation.source_lang,
						target_lang: translation.target_lang,
						entry_id: translation.id
					};
				} else {
					// It's text translation, switch to text input tab
					textInput = translation.original_text || "";
					activeTab = 2;
				}
				
				// Clear the session storage
				sessionStorage.removeItem('editTranslation');
			} catch (e) {
				console.error("Failed to load edit data:", e);
			}
		}
	});

	// Handlers
	async function handleTranslate() {
		// Use text input if on that tab and no original text
		if (activeTab === 2 && !originalText && textInput) {
			originalText = textInput;
		}
		
		if (!originalText) return;
		
		isLoading = true;
		errorMessage = "";
		
		try {
			const response = await translationAPI.translate({
				text: originalText,
				source_lang: sourceLang,
				target_lang: targetLang,
				entry_id: videoInfo?.entry_id
			});
			
			translatedText = response.translated_text;
			
			// If this was a YouTube transcript with translation, update the history entry
			if (videoInfo && videoInfo.entry_id) {
				// The backend will automatically update the existing entry
				console.log("Updated YouTube transcript translation in history");
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : "Translation failed";
		} finally {
			isLoading = false;
		}
	}

	async function handleFetchTranscript() {
		if (!youtubeUrl) return;
		
		isFetching = true;
		errorMessage = "";
		originalText = "";
		translatedText = "";
		
		try {
			const response = await youtubeAPI.fetchTranscript({
				url: youtubeUrl,
				source_lang: sourceLang === "auto" ? "en" : sourceLang,
				target_lang: targetLang,  // Now includes target language for automatic translation
				merge_lines: true
			});
			
			videoInfo = response;
			
			// Use processed version by default
			originalText = response.source_transcript_processed || response.source_transcript_raw || "";
			
			// Check if no transcript was fetched
			if (!originalText && response.available_languages.length > 0) {
				// Show helpful error with available languages
				const langs = response.available_languages.slice(0, 10).join(', ');
				errorMessage = `No transcript found for "${sourceLang}". Available: ${langs}...`;
			}
			
			// If we got a translated transcript, show it
			if (response.target_transcript_processed || response.target_transcript_raw) {
				translatedText = response.target_transcript_processed || response.target_transcript_raw || "";
			}
			
			// Show translation error if translation failed (transcript still fetched)
			if (response.translation_error) {
				errorMessage = response.translation_error;
			}
			
			// Update source language if it was detected
			if (response.source_lang && sourceLang === "auto") {
				sourceLang = response.source_lang;
			}
			
			// Show cached status if applicable
			if (response.cached) {
				console.log("Loaded cached transcript for", response.title);
			}
		} catch (error) {
			console.error("Fetch error:", error); // Debug log
			errorMessage = error instanceof Error ? error.message : "Failed to fetch transcript";
		} finally {
			isFetching = false;
		}
	}
	
	// Toggle between raw and processed transcript
	function toggleTranscriptView() {
		if (!videoInfo) return;
		
		if (showRawTranscript) {
			originalText = videoInfo.source_transcript_raw || "";
		} else {
			originalText = videoInfo.source_transcript_processed || "";
		}
	}

	// Export content as text file
	function exportContent() {
		if (!originalText && !translatedText) return;
		
		const title = videoInfo?.title || 'Translation';
		const lines = [title];
		
		if (videoInfo?.url) lines.push(`URL: ${videoInfo.url}`);
		lines.push(`Source Language: ${sourceLang}`);
		lines.push(`Target Language: ${targetLang}`);
		lines.push('');
		lines.push('ORIGINAL TEXT:');
		lines.push(originalText);
		
		if (translatedText) {
			lines.push('');
			lines.push('TRANSLATED TEXT:');
			lines.push(translatedText);
		}
		
		const content = lines.join('\n');
		const blob = new Blob([content], { type: 'text/plain' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${title.substring(0, 50).replace(/[^a-zA-Z0-9]/g, '_')}.txt`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	// Navigate to view page
	function goToView() {
		if (videoInfo?.entry_id) {
			window.location.href = `/view/${videoInfo.entry_id}`;
		}
	}

	// Copy modal
	let showCopyModal = false;
	let copiedWhat = "";

	function handleCopy() {
		showCopyModal = true;
	}

	async function copyContent(type: 'original' | 'translation' | 'both') {
		let text = '';
		if (type === 'original') {
			text = originalText;
		} else if (type === 'translation') {
			text = translatedText;
		} else {
			text = formatBothTexts(originalText, translatedText);
		}

		const success = await copyToClipboard(text);
		if (success) {
			copiedWhat = type;
			setTimeout(() => { copiedWhat = ""; }, 2000);
		}

		showCopyModal = false;
	}
</script>

<Content>
	<Grid>
		<!-- Edit Mode Notice -->
		{#if isEditMode}
			<Row>
				<Column sm={4} md={8} lg={12} xlg={12} max={12}>
					<InlineNotification
						kind="info"
						title="Review Mode"
						subtitle="You are reviewing a translation from your history. Make any edits below."
						hideCloseButton
						lowContrast
					/>
				</Column>
			</Row>
		{/if}
		
		<!-- Input Section -->
		<Row>
			<Column sm={4} md={8} lg={12} xlg={12} max={12}>
				<Tile light>
				<Tabs bind:selected={activeTab}>
					<Tab label="YouTube" icon={LogoYoutube} />
					<Tab label="Upload File" icon={Document} />
					<Tab label="Text Input" icon={TextAlignJustify} />
					
					<svelte:fragment slot="content">
						<!-- YouTube Tab -->
						<TabContent index={0}>
							<div class="tab-content">
								<TextInput
									labelText="YouTube URL"
									placeholder="https://www.youtube.com/watch?v=..."
									bind:value={youtubeUrl}
									helperText="Enter a YouTube video URL to fetch its transcript"
								/>
								<div class="button-group">
									<Button
										icon={LogoYoutube}
										on:click={handleFetchTranscript}
										disabled={!youtubeUrl || isFetching || isLoading}
									>
										{isFetching ? 'Fetching...' : 'Fetch Transcript'}
									</Button>
								</div>
							</div>
						</TabContent>

						<!-- File Upload Tab -->
						<TabContent index={1}>
							<div class="tab-content">
								<FileUploaderDropContainer
									labelText="Drag and drop files here or click to upload"
									bind:files
									accept={[".txt", ".srt", ".vtt", ".pdf", ".docx"]}
									multiple={false}
								/>
								{#if files.length > 0}
									{#each files as file}
										<FileUploaderItem
											name={file.name}
											status="edit"
											on:delete={() => files = []}
										/>
									{/each}
								{/if}
							</div>
						</TabContent>

						<!-- Text Input Tab -->
						<TabContent index={2}>
							<div class="tab-content">
								<TextArea
									labelText="Enter or paste text"
									placeholder="Enter text to translate..."
									rows={8}
									bind:value={textInput}
									helperText="Paste or type the text you want to translate"
								/>
							</div>
						</TabContent>
					</svelte:fragment>
				</Tabs>

				<!-- Language Selection -->
				<div class="language-selectors">
					<Select
						labelText="Source Language"
						bind:selected={sourceLang}
						helperText="Language of the original text"
					>
						{#each languages as lang}
							<SelectItem value={lang.id} text={lang.text} />
						{/each}
					</Select>

					<div class="arrow">→</div>

					<Select
						labelText="Target Language"
						bind:selected={targetLang}
						helperText="Language to translate to"
					>
						{#each languages.filter(l => l.id !== "auto") as lang}
							<SelectItem value={lang.id} text={lang.text} />
						{/each}
					</Select>
				</div>

				<!-- Action Buttons -->
				<div class="action-buttons">
					{#if isLoading}
						<InlineLoading description="Translating..." />
					{:else}
						<Button
							icon={Translate}
							on:click={handleTranslate}
							disabled={
								(activeTab === 0 && (!originalText || translatedText)) ||  // Disable if already translated from YouTube
								(activeTab === 1 && files.length === 0) ||
								(activeTab === 2 && !textInput)
							}
						>
							{translatedText && activeTab === 0 ? 'Already Translated' : 'Translate'}
						</Button>
					{/if}
				</div>
				</Tile>
			</Column>
		</Row>

		<!-- Results Section -->
		<Row>
			<Column sm={4} md={8} lg={12} xlg={12} max={12}>
				<Tile light>
				<div class="output-header">
					<h3>{isEditMode ? '📝 Reviewing Translation' : 'Translation Results'}</h3>
					{#if videoInfo}
						<Toggle
							size="sm"
							labelText="Show raw transcript"
							bind:toggled={showRawTranscript}
							on:toggle={toggleTranscriptView}
						/>
					{/if}
				</div>
				
				{#if errorMessage}
					<InlineNotification
						kind="error"
						title="Error"
						subtitle={errorMessage}
						hideCloseButton
					/>
				{/if}
				
				{#if videoInfo}
					<Tile class="video-info">
						<p class="video-title">📺 {videoInfo.title}</p>
						<p class="video-meta">Available languages: {videoInfo.available_languages.slice(0, 5).join(', ')}{videoInfo.available_languages.length > 5 ? '...' : ''}</p>
					</Tile>
				{/if}
				</Tile>
			</Column>
		</Row>
		
		<!-- Text Display - Two Columns -->
		<Row>
			<Column sm={4} md={4} lg={8} xlg={8} max={8}>
				<h4>Original Text {originalText ? `(${originalText.length} chars)` : ''}</h4>
				<Tile class="text-scroll-tile">
					<div class="text-content">
						{#if originalText}
							{#each originalText.split('\n\n') as paragraph, i}
								{#if paragraph.trim()}
									<p>{paragraph}</p>
								{/if}
							{/each}
						{:else}
							<p class="placeholder">Original text will appear here...</p>
						{/if}
					</div>
				</Tile>
			</Column>
			
			<Column sm={4} md={4} lg={8} xlg={8} max={8}>
				<h4>Translated Text</h4>
				<Tile class="text-scroll-tile">
					<div class="text-content">
						{#if translatedText}
							{#each translatedText.split('\n\n') as paragraph}
								<p>{paragraph}</p>
							{/each}
						{:else}
							<p class="placeholder">Translated text will appear here...</p>
						{/if}
					</div>
				</Tile>
			</Column>
		</Row>

		<!-- Action Buttons -->
		<Row>
			<Column sm={4} md={8} lg={12} xlg={12} max={12}>
				<div class="export-actions">
					{#if videoInfo?.entry_id}
						<Button
							kind="primary"
							icon={View}
							on:click={goToView}
						>
							Go to View
						</Button>
					{/if}
					<Button
						kind="secondary"
						icon={copiedWhat ? Checkmark : Copy}
						disabled={!originalText && !translatedText}
						on:click={handleCopy}
					>
						{copiedWhat ? 'Copied!' : 'Copy'}
					</Button>
					<Button
						kind="secondary"
						icon={DocumentDownload}
						disabled={!originalText && !translatedText}
						on:click={exportContent}
					>
						Export
					</Button>
				</div>
			</Column>
		</Row>
	</Grid>
</Content>

<!-- Copy Modal -->
<Modal
	passiveModal
	bind:open={showCopyModal}
	modalHeading="Copy to Clipboard"
	on:close={() => { showCopyModal = false; }}
>
	<div class="copy-modal-content">
		<h4 class="copy-modal-title">{videoInfo?.title || 'Translation'}</h4>
		<p class="copy-meta">{sourceLang} → {targetLang}</p>

		<div class="copy-options">
			<Button
				kind="tertiary"
				icon={Document}
				on:click={() => copyContent('original')}
				disabled={!originalText?.trim()}
			>
				Copy Original Text ({originalText?.length || 0} chars)
			</Button>

			<Button
				kind="tertiary"
				icon={Translate}
				on:click={() => copyContent('translation')}
				disabled={!translatedText?.trim()}
			>
				{#if translatedText?.trim()}
					Copy Translation ({translatedText.length} chars)
				{:else}
					Copy Translation (no translation available)
				{/if}
			</Button>

			<Button
				kind="tertiary"
				icon={Copy}
				on:click={() => copyContent('both')}
				disabled={!originalText?.trim()}
			>
				Copy Both ({(originalText?.length || 0) + (translatedText?.length || 0)} chars)
			</Button>
		</div>
	</div>
</Modal>

<style>
	:global(.bx--content) {
		background: var(--cds-ui-background);
		min-height: calc(100vh - 48px);
	}

	.button-group {
		margin-top: var(--cds-spacing-05);
	}

	.language-selectors {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		gap: var(--cds-spacing-06);
		align-items: end;
		margin: var(--cds-spacing-07) 0;
		max-width: 600px;
		margin-left: auto;
		margin-right: auto;
	}

	.arrow {
		font-size: 1.5rem;
		padding-bottom: var(--cds-spacing-03);
		color: var(--cds-text-secondary);
		text-align: center;
	}

	.action-buttons {
		display: flex;
		justify-content: center;
		margin-top: var(--cds-spacing-06);
	}

	.output-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--cds-spacing-06);
	}

	.output-header h3 {
		font-size: 1.25rem;
		margin: 0;
		color: var(--cds-text-primary);
		font-weight: 400;
	}
	
	.video-info {
		text-align: center;
		margin-bottom: var(--cds-spacing-06);
	}
	
	.video-title {
		font-weight: 600;
		margin-bottom: var(--cds-spacing-02);
		color: var(--cds-text-primary);
	}
	
	.video-meta {
		font-size: 0.875rem;
		color: var(--cds-text-secondary);
	}

	h4 {
		font-size: 0.875rem;
		font-weight: 600;
		margin-bottom: var(--cds-spacing-05);
		color: var(--cds-text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		text-align: center;
	}

	:global(.text-scroll-tile) {
		height: 500px;
		overflow-y: auto;
	}

	.text-content {
		font-size: 0.875rem;
		line-height: 1.6;
		color: var(--cds-text-primary);
	}
	
	.text-content p {
		margin-bottom: var(--cds-spacing-05);
	}
	
	.text-content p:last-child {
		margin-bottom: 0;
	}

	.placeholder {
		color: var(--cds-text-disabled);
		font-style: italic;
		text-align: center;
		padding: var(--cds-spacing-07);
	}

	.export-actions {
		display: flex;
		justify-content: center;
		gap: var(--cds-spacing-05);
		margin-top: var(--cds-spacing-07);
	}

	/* Copy Modal */
	.copy-modal-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--cds-text-primary);
		margin: 0 0 var(--cds-spacing-02) 0;
	}

	.copy-meta {
		font-size: 0.875rem;
		color: var(--cds-text-secondary);
		margin-bottom: var(--cds-spacing-06);
	}

	.copy-options {
		display: flex;
		flex-direction: column;
		gap: var(--cds-spacing-04);
	}

	.copy-options :global(.bx--btn) {
		width: 100%;
		max-width: none;
		justify-content: flex-start;
	}

	/* Responsive adjustments for mobile */
	@media (max-width: 768px) {
		:global(.text-scroll-tile) {
			height: 300px;
		}
		
		.language-selectors {
			grid-template-columns: 1fr;
			gap: var(--cds-spacing-05);
		}
		
		.arrow {
			display: none;
		}

		.output-header {
			flex-direction: column;
			gap: var(--cds-spacing-05);
			align-items: center;
		}
	}
</style>
