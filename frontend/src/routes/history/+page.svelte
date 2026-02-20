<script lang="ts">
	import {
		Content,
		DataTable,
		Toolbar,
		ToolbarContent,
		ToolbarSearch,
		Button,
		Modal,
		InlineNotification,
		ProgressIndicator,
		ProgressStep,
		Tile,
		Tag,
		SkeletonPlaceholder,
		InlineLoading,
		Pagination,
		OverflowMenu,
		OverflowMenuItem,
		Grid,
		Row,
		Column
	} from "carbon-components-svelte";
	
	import {
		Delete,
		View,
		TrashCan,
		Copy,
		Download,
		Edit,
		Checkmark,
		Document,
		Translate
	} from "carbon-icons-svelte";

	import { historyAPI } from "$lib/api";
	import { copyToClipboard, formatBothTexts } from "$lib/utils/clipboard";
	import { onMount } from "svelte";

	// State
	let translations = $state([]);
	let filteredTranslations = $state([]);
	let searchValue = $state("");
	let isLoading = $state(true);
	let error = $state("");
	let selectedTranslation = $state(null);
	let showDeleteModal = $state(false);
	let isDeleting = $state(false);
	let copiedId = $state<string | null>(null);
	
	// Responsive state
	let isMobile = $state(false);
	let windowWidth = $state(0);
	
	// Pagination
	let page = $state(1);
	let pageSize = $state(10);
	let totalItems = $derived(filteredTranslations.length);
	
	// Table headers
	const headers = [
		{ key: "created_at", value: "Date" },
		{ key: "title", value: "Title" },
		{ key: "source_lang", value: "From" },
		{ key: "target_lang", value: "To" },
		{ key: "provider", value: "Provider" },
		{ key: "actions", value: "Actions", sort: false }
	];
	
	// Check if mobile
	$effect(() => {
		isMobile = windowWidth < 768;
	});

	onMount(() => {
		loadHistory();
	});

	async function loadHistory() {
		try {
			isLoading = true;
			error = "";
			
			const offset = (page - 1) * pageSize;
			const response = await historyAPI.getHistory(pageSize, offset);
			translations = response.map(item => ({
				...item,
				id: item.id,
				created_at: new Date(item.created_at).toLocaleDateString() + " " + new Date(item.created_at).toLocaleTimeString(),
				title: item.title || getTextPreview(item.original_text),
				original_preview: getTextPreview(item.original_text),
				translated_preview: getTextPreview(item.translated_text)
			}));
			
			// Apply search filter
			applySearch();
		} catch (err) {
			error = err instanceof Error ? err.message : "Failed to load history";
		} finally {
			isLoading = false;
		}
	}

	function getTextPreview(text, maxLength = 80) {
		if (!text) return "No text";
		return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
	}

	function applySearch() {
		if (!searchValue.trim()) {
			filteredTranslations = translations;
		} else {
			const search = searchValue.toLowerCase();
			filteredTranslations = translations.filter(item =>
				item.title.toLowerCase().includes(search) ||
				item.source_lang.toLowerCase().includes(search) ||
				item.target_lang.toLowerCase().includes(search) ||
				item.provider.toLowerCase().includes(search) ||
				item.original_text.toLowerCase().includes(search) ||
				item.translated_text.toLowerCase().includes(search)
			);
		}
	}

	function handleView(translation) {
		// Navigate to the view page
		window.location.href = `/view/${translation.id}`;
	}

	function handleEdit(translation) {
		// Navigate to main page with the translation loaded for editing
		// Store the translation data in sessionStorage to load on the main page
		sessionStorage.setItem('editTranslation', JSON.stringify(translation));
		window.location.href = '/';
	}

	function handleDelete(translation) {
		selectedTranslation = translation;
		showDeleteModal = true;
	}

	async function confirmDelete() {
		if (!selectedTranslation) return;
		
		try {
			isDeleting = true;
			await historyAPI.deleteTranslation(selectedTranslation.id);
			
			// Remove from local state
			translations = translations.filter(t => t.id !== selectedTranslation.id);
			applySearch();
			
			showDeleteModal = false;
			selectedTranslation = null;
		} catch (err) {
			error = err instanceof Error ? err.message : "Failed to delete translation";
		} finally {
			isDeleting = false;
		}
	}

	// Copy modal state
	let showCopyModal = $state(false);
	let copyTarget = $state<any>(null);

	function handleCopy(translation: any) {
		copyTarget = translation;
		showCopyModal = true;
	}

	async function copyContent(type: 'original' | 'translation' | 'both') {
		if (!copyTarget) return;

		let text = '';
		if (type === 'original') {
			text = copyTarget.original_text;
		} else if (type === 'translation') {
			text = copyTarget.translated_text;
		} else {
			text = formatBothTexts(copyTarget.original_text, copyTarget.translated_text);
		}

		const success = await copyToClipboard(text);
		if (success) {
			copiedId = copyTarget.id;
			setTimeout(() => { copiedId = null; }, 2000);
		}

		showCopyModal = false;
		copyTarget = null;
	}

	function downloadTranslation(translation) {
		const content = `Original (${translation.source_lang}):\n${translation.original_text}\n\nTranslated (${translation.target_lang}):\n${translation.translated_text}`;
		const blob = new Blob([content], { type: 'text/plain' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `translation-${translation.id}.txt`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	// Reactive search
	$effect(() => {
		if (searchValue !== undefined) applySearch();
	});
</script>

<svelte:window bind:innerWidth={windowWidth} />

<Content>
	<Grid fullWidth>
		<!-- Title Section -->
		<Row>
			<Column sm={4} md={8} lg={12} xlg={14} max={14}>
				<div class="title-section">
					<h1>Translation History</h1>
					<p class="helper-text">
						View and manage your past translations and YouTube transcripts.
					</p>
				</div>
			</Column>
		</Row>

		<!-- Error Notification -->
		{#if error}
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					<InlineNotification
						kind="error"
						title="Error"
						subtitle={error}
						hideCloseButton
						lowContrast
					/>
				</Column>
			</Row>
		{/if}

		<!-- Search Bar (Always visible) -->
		{#if !isLoading && translations.length > 0}
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					<Tile light>
						<Toolbar>
							<ToolbarContent>
								<ToolbarSearch
									persistent
									placeholder="Search translations..."
									bind:value={searchValue}
								/>
							</ToolbarContent>
						</Toolbar>
					</Tile>
				</Column>
			</Row>
		{/if}

		{#if isLoading}
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					<SkeletonPlaceholder style="height: 400px; width: 100%;" />
				</Column>
			</Row>
		{:else if translations.length === 0}
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					<Tile>
						<h3>No translations found</h3>
						<p>Start translating content to see your history here.</p>
						<Button href="/">Start Translating</Button>
					</Tile>
				</Column>
			</Row>
		{:else if isMobile}
			<!-- Mobile: Card Layout -->
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					{#each filteredTranslations as translation}
						<Tile class="translation-card">
							<div class="card-header">
								<h4 class="card-title">{translation.title}</h4>
								<OverflowMenu flipped>
									<OverflowMenuItem text="View" on:click={() => handleView(translation)} />
									<OverflowMenuItem text="Edit" on:click={() => handleEdit(translation)} />
									<OverflowMenuItem text={copiedId === translation.id ? "Copied!" : "Copy"} on:click={() => handleCopy(translation)} />
									<OverflowMenuItem text="Download" on:click={() => downloadTranslation(translation)} />
									<OverflowMenuItem danger text="Delete" on:click={() => handleDelete(translation)} />
								</OverflowMenu>
							</div>
							
							<div class="card-meta">
								<div class="meta-row">
									<Tag type="outline" size="sm">{translation.source_lang} → {translation.target_lang}</Tag>
									<Tag type="blue" size="sm">{translation.provider}</Tag>
								</div>
								<p class="date-text">{translation.created_at}</p>
							</div>
							
							<div class="card-preview">
								<p class="preview-text">{translation.original_preview}</p>
							</div>
						</Tile>
					{/each}
				</Column>
			</Row>
		{:else}
			<!-- Desktop: Table Layout -->
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					<Tile light>
						<DataTable
							{headers}
							rows={filteredTranslations}
							size="short"
							zebra
						>
							<svelte:fragment slot="cell" let:row let:cell>
								{#if cell.key === "actions"}
									<div class="action-buttons">
										<Button
											kind="ghost"
											size="sm"
											iconDescription="View details"
											icon={View}
											on:click={() => handleView(row)}
										/>
										<Button
											kind="ghost"
											size="sm"
											iconDescription="Edit/Review"
											icon={Edit}
											on:click={() => handleEdit(row)}
										/>
										<Button
											kind="ghost"
											size="sm"
											iconDescription={copiedId === row.id ? "Copied!" : "Copy text"}
											icon={copiedId === row.id ? Checkmark : Copy}
											on:click={() => handleCopy(row)}
										/>
										<Button
											kind="ghost"
											size="sm"
											iconDescription="Download"
											icon={Download}
											on:click={() => downloadTranslation(row)}
										/>
										<Button
											kind="danger-ghost"
											size="sm"
											iconDescription="Delete"
											icon={Delete}
											on:click={() => handleDelete(row)}
										/>
									</div>
								{:else if cell.key === "source_lang" || cell.key === "target_lang"}
									<Tag type="outline">{cell.value}</Tag>
								{:else if cell.key === "provider"}
									<Tag type="blue">{cell.value}</Tag>
								{:else if cell.key === "title"}
									<div class="title-cell">
										<span class="title-text">{cell.value}</span>
									</div>
								{:else}
									{cell.value}
								{/if}
							</svelte:fragment>
						</DataTable>
					</Tile>
				</Column>
			</Row>
		{/if}

		<!-- Pagination -->
		{#if !isLoading && totalItems > pageSize}
			<Row>
				<Column sm={4} md={8} lg={12} xlg={14} max={14}>
					<Pagination
						bind:page
						bind:pageSize
						totalItems={totalItems}
						pageSizeInputDisabled
					/>
				</Column>
			</Row>
		{/if}
	</Grid>
</Content>


<!-- Delete Confirmation Modal -->
<Modal
	danger
	bind:open={showDeleteModal}
	modalHeading="Delete Translation"
	primaryButtonText="Delete"
	secondaryButtonText="Cancel"
	primaryButtonDisabled={isDeleting}
	on:click:button--secondary={() => showDeleteModal = false}
	on:submit={confirmDelete}
>
	{#if selectedTranslation}
		<p>Are you sure you want to delete this translation?</p>
		<div class="delete-preview">
			<strong>Title:</strong> {selectedTranslation.title}<br>
			<strong>Date:</strong> {selectedTranslation.created_at}
		</div>
		
		{#if isDeleting}
			<InlineLoading description="Deleting..." />
		{/if}
	{/if}
</Modal>

<!-- Copy Modal -->
<Modal
	passiveModal
	bind:open={showCopyModal}
	modalHeading="Copy to Clipboard"
	on:close={() => { showCopyModal = false; copyTarget = null; }}
>
	{#if copyTarget}
		<div class="copy-modal-content">
			<h4 class="copy-modal-title">{copyTarget.title}</h4>
			<p class="copy-meta">
				{copyTarget.source_lang} → {copyTarget.target_lang} · {copyTarget.provider}
			</p>

			<div class="copy-options">
				<Button
					kind="tertiary"
					icon={Document}
					on:click={() => copyContent('original')}
					disabled={!copyTarget.original_text?.trim()}
				>
					Copy Original Text ({copyTarget.original_text?.length || 0} chars)
				</Button>

				<Button
					kind="tertiary"
					icon={Translate}
					on:click={() => copyContent('translation')}
					disabled={!copyTarget.translated_text?.trim()}
				>
					{#if copyTarget.translated_text?.trim()}
						Copy Translation ({copyTarget.translated_text.length} chars)
					{:else}
						Copy Translation (no translation available)
					{/if}
				</Button>

				<Button
					kind="tertiary"
					icon={Copy}
					on:click={() => copyContent('both')}
					disabled={!copyTarget.original_text?.trim()}
				>
					Copy Both ({(copyTarget.original_text?.length || 0) + (copyTarget.translated_text?.length || 0)} chars)
				</Button>
			</div>
		</div>
	{/if}
</Modal>

<style>
	/* Title Section */
	.title-section {
		text-align: center;
		max-width: 600px;
		margin: 0 auto var(--cds-spacing-07) auto;
	}

	h1 {
		font-size: 2.5rem;
		margin-bottom: var(--cds-spacing-03);
		color: var(--cds-text-primary);
		font-weight: 300;
	}

	.helper-text {
		color: var(--cds-text-secondary);
		font-size: 1rem;
		line-height: 1.5;
	}

	h3 {
		margin-bottom: var(--cds-spacing-05);
		color: var(--cds-text-primary);
	}

	/* Table Cells */
	.action-buttons {
		display: flex;
		gap: var(--cds-spacing-03);
		align-items: center;
	}

	.title-cell {
		max-width: 300px;
	}

	.title-text {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.delete-preview {
		padding: var(--cds-spacing-05);
		background: var(--cds-ui-02);
		border-radius: 4px;
		margin: var(--cds-spacing-05) 0;
		color: var(--cds-text-secondary);
		font-size: 0.875rem;
	}

	/* Mobile Cards */
	:global(.translation-card) {
		margin-bottom: var(--cds-spacing-05);
		background: var(--cds-ui-background);
		border: 1px solid var(--cds-ui-03);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--cds-spacing-05);
	}

	.card-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--cds-text-primary);
		margin: 0;
		flex: 1;
		margin-right: var(--cds-spacing-05);
		line-height: 1.3;
	}

	.card-meta {
		margin-bottom: var(--cds-spacing-05);
	}

	.meta-row {
		display: flex;
		gap: var(--cds-spacing-03);
		align-items: center;
		margin-bottom: var(--cds-spacing-03);
		flex-wrap: wrap;
	}

	.date-text {
		font-size: 0.875rem;
		color: var(--cds-text-secondary);
		margin: 0;
	}

	.card-preview {
		border-top: 1px solid var(--cds-ui-03);
		padding-top: var(--cds-spacing-05);
	}

	.preview-text {
		font-size: 0.875rem;
		color: var(--cds-text-secondary);
		line-height: 1.4;
		margin: 0;
		overflow: hidden;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
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

	/* Responsive Design */
	@media (max-width: 768px) {
		h1 {
			font-size: 2rem;
		}

		.card-title {
			font-size: 0.875rem;
		}

		.meta-row {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--cds-spacing-02);
		}
	}
</style>