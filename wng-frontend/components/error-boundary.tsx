'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  /** Optional custom fallback. When omitted the default error card is shown. */
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Log to an external service in production if needed
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    return (
      <Card className="mx-auto mt-12 max-w-lg border-destructive/40">
        <CardContent className="flex flex-col items-center py-14 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle className="h-6 w-6 text-destructive" />
          </div>

          <h2 className="text-lg font-semibold">Something went wrong</h2>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>

          <Button
            variant="outline"
            className="mt-6"
            onClick={this.handleReset}
          >
            Try again
          </Button>
        </CardContent>
      </Card>
    );
  }
}
