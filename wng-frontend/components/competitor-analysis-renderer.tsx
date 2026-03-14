import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Lightbulb, Target, TrendingUp, Presentation, AlertCircle, Zap, Info } from 'lucide-react';

interface AnalysisSection {
    title: string;
    content: string | string[];
}

interface CompetitorAnalysisRendererProps {
    analysis: string;
}

export function CompetitorAnalysisRenderer({ analysis }: CompetitorAnalysisRendererProps) {
    if (!analysis) return null;

    let sections: AnalysisSection[] = [];
    let summary = '';

    // Attempt to parse as JSON first
    try {
        const data = JSON.parse(analysis);
        if (data.summary) {
            summary = data.summary;
        }
        if (Array.isArray(data.sections)) {
            sections = data.sections.map((s: any) => ({
                title: s.title || 'Section',
                content: s.content || [],
            }));
        }
    } catch (error) {
        // Fallback: Legacy parsing for raw plain-text analysis responses
        const lines = analysis.split('\n');
        let currentSectionTitle = 'Summary';
        let currentContent: string[] = [];

        const headerRegex = /^(\d+[\.\)])\s+(.*)$/;

        lines.forEach((line) => {
            const match = line.match(headerRegex);
            if (match) {
                if (currentContent.length > 0 || currentSectionTitle === 'Summary') {
                    if (!(currentSectionTitle === 'Summary' && currentContent.join('').trim() === '')) {
                        sections.push({
                            title: currentSectionTitle,
                            content: currentContent.join('\n').trim(),
                        });
                    }
                }
                currentSectionTitle = match[2].trim();
                currentContent = [];
            } else {
                currentContent.push(line);
            }
        });

        if (currentContent.length > 0) {
            sections.push({
                title: currentSectionTitle,
                content: currentContent.join('\n').trim(),
            });
        }
    }

    // Add summary as the first section if JSON parsing found one and it isn't already there
    if (summary && (sections.length === 0 || sections[0].title !== 'Summary')) {
        sections.unshift({ title: 'Summary', content: summary });
    }

    // Determine icons based on common titles
    const getIconForTitle = (title: string) => {
        const lower = title.toLowerCase();
        if (lower.includes('strategy') || lower.includes('pillar')) return <Presentation className="w-5 h-5 text-blue-500" />;
        if (lower.includes('engagement')) return <TrendingUp className="w-5 h-5 text-apple-blue" />;
        if (lower.includes('positioning') || lower.includes('messaging')) return <Target className="w-5 h-5 text-purple-500" />;
        if (lower.includes('strength') || lower.includes('weakness')) return <AlertCircle className="w-5 h-5 text-orange-500" />;
        if (lower.includes('opportunit')) return <Lightbulb className="w-5 h-5 text-yellow-500" />;
        if (lower.includes('action') || lower.includes('recommendation')) return <Zap className="w-5 h-5 text-green-500" />;
        if (lower === 'summary' || lower === 'overview') return <Info className="w-5 h-5 text-indigo-400" />;
        return <Target className="w-5 h-5 text-ink-soft" />;
    };

    // Helper to render markdown-like bullets
    const renderContent = (content: string | string[]) => {
        if (Array.isArray(content)) {
            return content.map((item, i) => {
                // Highlight content before a colon if it exists
                const parts = item.split(':');
                if (parts.length > 1) {
                    return (
                        <li key={i} className="ml-4 list-disc mb-2 text-sm text-ink leading-relaxed">
                            <strong className="font-semibold text-ink">{parts[0].trim()}:</strong>
                            {parts.slice(1).join(':')}
                        </li>
                    );
                }
                return <li key={i} className="ml-4 list-disc mb-2 text-sm text-ink leading-relaxed">{item}</li>;
            });
        }

        // Legacy text parsing fallback
        return content.split('\n').map((line, i) => {
            const trimmed = line.trim();
            if (!trimmed) return <br key={i} />;

            if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
                const parts = trimmed.substring(1).split(':');
                if (parts.length > 1) {
                    return (
                        <li key={i} className="ml-4 list-disc mb-2 text-sm text-ink leading-relaxed">
                            <strong className="font-semibold text-ink">{parts[0].trim()}:</strong>
                            {parts.slice(1).join(':')}
                        </li>
                    );
                }
                return <li key={i} className="ml-4 list-disc mb-2 text-sm text-ink leading-relaxed">{trimmed.substring(1).trim()}</li>;
            }

            return <p key={i} className="mb-2 text-sm text-ink leading-relaxed">{trimmed}</p>;
        });
    };

    if (sections.length === 0) {
        return (
            <div className="rounded-2xl apple-glass p-6">
                <p className="whitespace-pre-wrap break-words text-sm text-ink">{analysis}</p>
            </div>
        );
    }

    return (
        <Tabs defaultValue={sections[0].title} className="w-full">
            <div className="overflow-x-auto pb-2 mb-4 scrollbar-none">
                <TabsList className="inline-flex h-10 items-center justify-start rounded-md bg-surface-2 p-1 text-ink-soft">
                    {sections.map((section, idx) => {
                        let shortTitle = section.title;
                        if (shortTitle === 'Summary') shortTitle = 'Overview';
                        else if (shortTitle.toLowerCase().includes('strategy')) shortTitle = 'Strategy';
                        else if (shortTitle.toLowerCase().includes('engagement')) shortTitle = 'Engagement';
                        else if (shortTitle.toLowerCase().includes('positioning')) shortTitle = 'Positioning';
                        else if (shortTitle.toLowerCase().includes('strength') || shortTitle.toLowerCase().includes('weakness')) shortTitle = 'SWOT';
                        else if (shortTitle.toLowerCase().includes('opportunities')) shortTitle = 'Opportunities';
                        else if (shortTitle.toLowerCase().includes('action') || shortTitle.toLowerCase().includes('recommendation')) shortTitle = 'Actions';

                        return (
                            <TabsTrigger
                                key={idx}
                                value={section.title}
                                className="inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-ink data-[state=active]:shadow-sm"
                            >
                                {shortTitle}
                            </TabsTrigger>
                        );
                    })}
                </TabsList>
            </div>

            {sections.map((section, idx) => (
                <TabsContent key={idx} value={section.title} className="mt-0 outline-none">
                    <Card className="rounded-2xl border-none apple-glass shadow-apple-md overflow-hidden">
                        <CardHeader className="pb-3 flex flex-row items-center gap-3">
                            {section.title !== 'Summary' && (
                                <div className="p-2 bg-background rounded-md border border-white/[0.06]">
                                    {getIconForTitle(section.title)}
                                </div>
                            )}
                            <div>
                                <CardTitle className="text-lg font-semibold text-ink">{section.title}</CardTitle>
                                {section.title !== 'Summary' && (
                                    <CardDescription className="text-xs text-ink-soft mt-1">Detailed analysis points</CardDescription>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="text-sm text-ink">
                                <ul className="space-y-1">
                                    {renderContent(section.content)}
                                </ul>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            ))}
        </Tabs>
    );
}
