import { writable } from 'svelte/store';

export const settings = writable({
    default_target_language: 'en',
    auto_translate: true,
    libretranslate_url: 'http://libretranslate:5000',
    default_view_mode: 'side-by-side',
    font_size: 'medium',
    theme: 'white',
    highlight_color: '#0f62fe',
    auto_paragraph_mobile: true,
    auto_scroll_speed: 1.0,
    highlight_active: true,
    default_playback_speed: 1.0,
    history_retention_days: null,
    api_timeout: 30,
    cache_duration_minutes: 60,
    debug_mode: false
});

export async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const data = await response.json();
            settings.set(data);
            return data;
        }
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

export async function updateSettings(updates) {
    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        if (response.ok) {
            const data = await response.json();
            settings.set(data);
            return data;
        }
    } catch (error) {
        console.error('Failed to update settings:', error);
        throw error;
    }
}

export async function resetSettings() {
    try {
        const response = await fetch('/api/settings/reset', {
            method: 'POST'
        });
        if (response.ok) {
            const data = await response.json();
            settings.set(data);
            return data;
        }
    } catch (error) {
        console.error('Failed to reset settings:', error);
        throw error;
    }
}