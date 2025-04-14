declare module 'msw' {
  export const rest: {
    get: (url: string, resolver: (req: RestRequest, res: ResponseComposition, ctx: RestContext) => any) => any;
    post: (url: string, resolver: (req: RestRequest, res: ResponseComposition, ctx: RestContext) => any) => any;
    put: (url: string, resolver: (req: RestRequest, res: ResponseComposition, ctx: RestContext) => any) => any;
    delete: (url: string, resolver: (req: RestRequest, res: ResponseComposition, ctx: RestContext) => any) => any;
    patch: (url: string, resolver: (req: RestRequest, res: ResponseComposition, ctx: RestContext) => any) => any;
  };
  
  export interface RestRequest {
    url: URL;
    params: Record<string, string>;
    body: any;
    headers: Headers;
  }
  
  export interface ResponseComposition {
    (ctx: RestContext): any;
  }
  
  export interface RestContext {
    status: (statusCode: number) => RestContext;
    json: (body: any) => RestContext;
    text: (text: string) => RestContext;
    xml: (xml: string) => RestContext;
    delay: (ms: number) => RestContext;
    fetch: (req: RestRequest) => Promise<Response>;
    cookie: (name: string, value: string) => RestContext;
    set: (name: string, value: string) => RestContext;
  }
}

declare module 'msw/node' {
  import { RequestHandler } from 'msw';
  
  export function setupServer(...handlers: any[]): {
    listen: (options?: { onUnhandledRequest?: 'error' | 'warn' | 'bypass' }) => void;
    close: () => void;
    resetHandlers: () => void;
    use: (...handlers: any[]) => void;
  };
} 