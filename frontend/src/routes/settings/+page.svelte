<script>
    import { onMount } from 'svelte';
    import {
        Grid, Row, Column,
        Form, FormGroup, TextInput, Select, SelectItem,
        Toggle, NumberInput,
        Button, InlineNotification,
        Tabs, Tab, TabContent,
        Modal
    } from 'carbon-components-svelte';
    import { Save, Reset, Download, Upload } from 'carbon-icons-svelte';
    import { settings, loadSettings, updateSettings, resetSettings } from '$lib/stores/settings.js';
    import { getVersion } from '$lib/api';
    
    let currentSettings = $state({});
    let originalSettings = $state({});
    let notification = $state({ show: false, kind: 'success', title: '', subtitle: '' });
    let resetModalOpen = $state(false);
    let hasChanges = $derived(JSON.stringify(currentSettings) !== JSON.stringify(originalSettings));
    let versionInfo = $state({ version: '', build_date: '', git_commit: '' });
    
    const languages = [
        { value: 'en', text: 'English' },
        { value: 'es', text: 'Spanish' },
        { value: 'fr', text: 'French' },
        { value: 'de', text: 'German' },
        { value: 'it', text: 'Italian' },
        { value: 'pt', text: 'Portuguese' },
        { value: 'ru', text: 'Russian' },
        { value: 'zh', text: 'Chinese' },
        { value: 'ja', text: 'Japanese' },
        { value: 'ko', text: 'Korean' },
        { value: 'ar', text: 'Arabic' },
        { value: 'hi', text: 'Hindi' },
        { value: 'nl', text: 'Dutch' }
    ];
    
    const themes = [
        { value: 'white', text: 'White (Light)' },
        { value: 'g10', text: 'Gray 10 (Light)' },
        { value: 'g80', text: 'Gray 80 (Dark)' },
        { value: 'g90', text: 'Gray 90 (Dark)' },
        { value: 'g100', text: 'Gray 100 (Dark)' }
    ];
    
    const fontSizes = [
        { value: 'small', text: 'Small' },
        { value: 'medium', text: 'Medium' },
        { value: 'large', text: 'Large' }
    ];
    
    const viewModes = [
        { value: 'side-by-side', text: 'Side by Side' },
        { value: 'paragraph', text: 'Paragraph by Paragraph' }
    ];
    
    onMount(async () => {
        const loaded = await loadSettings();
        if (loaded) {
            currentSettings = { ...loaded };
            originalSettings = { ...loaded };
        }
        try {
            versionInfo = await getVersion();
        } catch (e) {
            // Version info is non-critical
        }
    });
    
    async function saveSettings() {
        try {
            await updateSettings(currentSettings);
            originalSettings = { ...currentSettings };
            // Apply theme immediately
            if (currentSettings.theme) {
                document.documentElement.setAttribute('theme', currentSettings.theme);
            }
            showNotification('success', 'Settings saved', 'Your settings have been saved successfully.');
        } catch (error) {
            showNotification('error', 'Save failed', 'Failed to save settings. Please try again.');
        }
    }
    
    // Apply theme changes immediately when selecting
    $effect(() => {
        if (currentSettings.theme && currentSettings.theme !== originalSettings.theme) {
            document.documentElement.setAttribute('theme', currentSettings.theme);
        }
    });
    
    async function handleReset() {
        try {
            const reset = await resetSettings();
            currentSettings = { ...reset };
            originalSettings = { ...reset };
            resetModalOpen = false;
            showNotification('info', 'Settings reset', 'All settings have been reset to defaults.');
        } catch (error) {
            showNotification('error', 'Reset failed', 'Failed to reset settings. Please try again.');
        }
    }
    
    async function exportSettings() {
        try {
            const response = await fetch('/api/settings/export');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ytt-settings.json';
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('success', 'Export complete', 'Settings exported successfully.');
        } catch (error) {
            showNotification('error', 'Export failed', 'Failed to export settings.');
        }
    }
    
    async function importSettings(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        try {
            const text = await file.text();
            const imported = JSON.parse(text);
            const response = await fetch('/api/settings/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(imported)
            });
            
            if (response.ok) {
                const data = await response.json();
                currentSettings = { ...data };
                originalSettings = { ...data };
                showNotification('success', 'Import complete', 'Settings imported successfully.');
            } else {
                throw new Error('Import failed');
            }
        } catch (error) {
            showNotification('error', 'Import failed', 'Failed to import settings. Please check the file.');
        }
    }
    
    function showNotification(kind, title, subtitle) {
        notification = { show: true, kind, title, subtitle };
        setTimeout(() => {
            notification.show = false;
        }, 5000);
    }
</script>

<Grid>
    <Row>
        <Column>
            <h1>Settings</h1>
            
            {#if notification.show}
                <InlineNotification
                    kind={notification.kind}
                    title={notification.title}
                    subtitle={notification.subtitle}
                    lowContrast
                    hideCloseButton
                />
            {/if}
        </Column>
    </Row>
    
    <Row>
        <Column>
            <Tabs>
                <Tab label="Translation" />
                <Tab label="Display" />
                <Tab label="Playback" />
                <Tab label="Advanced" />
                
                <svelte:fragment slot="content">
                    <TabContent>
                        <Form>
                            <FormGroup>
                                <Select
                                    labelText="Default Target Language"
                                    bind:selected={currentSettings.default_target_language}
                                >
                                    {#each languages as lang}
                                        <SelectItem value={lang.value} text={lang.text} />
                                    {/each}
                                </Select>
                            </FormGroup>
                            
                            <FormGroup>
                                <Toggle
                                    labelText="Auto-translate on fetch"
                                    labelA="Off"
                                    labelB="On"
                                    bind:toggled={currentSettings.auto_translate}
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <TextInput
                                    labelText="LibreTranslate Server URL"
                                    placeholder="http://libretranslate:5000"
                                    bind:value={currentSettings.libretranslate_url}
                                    helperText="URL of your LibreTranslate instance"
                                />
                            </FormGroup>
                        </Form>
                    </TabContent>
                    
                    <TabContent>
                        <Form>
                            <FormGroup>
                                <Select
                                    labelText="Default View Mode"
                                    bind:selected={currentSettings.default_view_mode}
                                >
                                    {#each viewModes as mode}
                                        <SelectItem value={mode.value} text={mode.text} />
                                    {/each}
                                </Select>
                            </FormGroup>
                            
                            <FormGroup>
                                <Select
                                    labelText="Font Size"
                                    bind:selected={currentSettings.font_size}
                                >
                                    {#each fontSizes as size}
                                        <SelectItem value={size.value} text={size.text} />
                                    {/each}
                                </Select>
                            </FormGroup>
                            
                            <FormGroup>
                                <Select
                                    labelText="Theme"
                                    bind:selected={currentSettings.theme}
                                >
                                    {#each themes as theme}
                                        <SelectItem value={theme.value} text={theme.text} />
                                    {/each}
                                </Select>
                            </FormGroup>
                            
                            <FormGroup>
                                <TextInput
                                    labelText="Highlight Color"
                                    placeholder="#0f62fe"
                                    bind:value={currentSettings.highlight_color}
                                    helperText="Color for paragraph linking highlight"
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <Toggle
                                    labelText="Auto-enable paragraph view on mobile"
                                    labelA="Off"
                                    labelB="On"
                                    bind:toggled={currentSettings.auto_paragraph_mobile}
                                />
                            </FormGroup>
                        </Form>
                    </TabContent>
                    
                    <TabContent>
                        <Form>
                            <FormGroup>
                                <NumberInput
                                    label="Auto-scroll Speed"
                                    bind:value={currentSettings.auto_scroll_speed}
                                    min={0.5}
                                    max={3.0}
                                    step={0.1}
                                    helperText="Speed multiplier for auto-scrolling (0.5 - 3.0)"
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <Toggle
                                    labelText="Highlight active paragraph"
                                    labelA="Off"
                                    labelB="On"
                                    bind:toggled={currentSettings.highlight_active}
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <NumberInput
                                    label="Default Playback Speed"
                                    bind:value={currentSettings.default_playback_speed}
                                    min={0.25}
                                    max={2.0}
                                    step={0.25}
                                    helperText="Default video playback speed (0.25 - 2.0)"
                                />
                            </FormGroup>
                        </Form>
                    </TabContent>
                    
                    <TabContent>
                        <Form>
                            <FormGroup>
                                <NumberInput
                                    label="History Retention (days)"
                                    bind:value={currentSettings.history_retention_days}
                                    min={0}
                                    max={365}
                                    allowEmpty
                                    helperText="Number of days to keep history (empty = unlimited)"
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <NumberInput
                                    label="API Timeout (seconds)"
                                    bind:value={currentSettings.api_timeout}
                                    min={10}
                                    max={120}
                                    helperText="Request timeout for YouTube/translation APIs"
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <NumberInput
                                    label="Cache Duration (minutes)"
                                    bind:value={currentSettings.cache_duration_minutes}
                                    min={0}
                                    max={1440}
                                    helperText="How long to cache fetched transcripts (0 = no cache)"
                                />
                            </FormGroup>
                            
                            <FormGroup>
                                <Toggle
                                    labelText="Debug Mode"
                                    labelA="Off"
                                    labelB="On"
                                    bind:toggled={currentSettings.debug_mode}
                                    helperText="Show technical information for troubleshooting"
                                />
                            </FormGroup>
                        </Form>
                    </TabContent>
                </svelte:fragment>
            </Tabs>
        </Column>
    </Row>
    
    <Row>
        <Column>
            <div class="button-group">
                <Button 
                    icon={Save}
                    disabled={!hasChanges}
                    onclick={saveSettings}
                >
                    Save Settings
                </Button>
                
                <Button
                    kind="secondary"
                    icon={Reset}
                    onclick={() => resetModalOpen = true}
                >
                    Reset to Defaults
                </Button>
                
                <Button
                    kind="tertiary"
                    icon={Download}
                    onclick={exportSettings}
                >
                    Export
                </Button>
                
                <Button
                    kind="tertiary"
                    icon={Upload}
                    onclick={() => document.getElementById('import-file').click()}
                >
                    Import
                </Button>
                <input
                    id="import-file"
                    type="file"
                    accept=".json"
                    style="display: none"
                    onchange={importSettings}
                />
            </div>
        </Column>
    </Row>
    
    <!-- About / Version Info -->
    {#if versionInfo.version}
    <Row>
        <Column>
            <div class="version-info">
                <span>YTT v{versionInfo.version}</span>
                {#if versionInfo.build_date && versionInfo.build_date !== 'dev' && versionInfo.build_date !== 'unknown'}
                    <span>Built {new Date(versionInfo.build_date).toLocaleDateString()} {new Date(versionInfo.build_date).toLocaleTimeString()}</span>
                {:else}
                    <span>Development build</span>
                {/if}
                {#if versionInfo.git_commit && versionInfo.git_commit !== 'dev' && versionInfo.git_commit !== 'unknown'}
                    <span>Commit {versionInfo.git_commit}</span>
                {/if}
            </div>
        </Column>
    </Row>
    {/if}
</Grid>

<Modal
    bind:open={resetModalOpen}
    modalHeading="Reset Settings"
    primaryButtonText="Reset"
    secondaryButtonText="Cancel"
    on:click:button--primary={handleReset}
    on:click:button--secondary={() => resetModalOpen = false}
    danger
>
    <p>Are you sure you want to reset all settings to their default values? This action cannot be undone.</p>
</Modal>

<style>
    h1 {
        margin-bottom: 32px;
    }
    
    .button-group {
        display: flex;
        gap: 16px;
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid #e0e0e0;
    }
    
    .version-info {
        display: flex;
        gap: 16px;
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid #e0e0e0;
        font-size: 0.75rem;
        color: #a8a8a8;
    }
    
    @media (max-width: 768px) {
        .button-group {
            flex-direction: column;
        }
        
        .button-group :global(.bx--btn) {
            width: 100%;
            max-width: none;
        }
        
        .version-info {
            flex-direction: column;
            gap: 4px;
        }
    }
</style>