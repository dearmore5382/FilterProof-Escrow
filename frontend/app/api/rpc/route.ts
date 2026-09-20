const upstream = 'https://studio.genlayer.com/api';
const allowedMethods = new Set([
  'eth_chainId',
  'eth_estimateGas',
  'eth_gasPrice',
  'eth_getTransactionByHash',
  'eth_getTransactionCount',
  'gen_call',
  'gen_getContractCode',
]);

export async function POST(request: Request) {
  const length = Number(request.headers.get('content-length') ?? '0');
  if (length > 64_000)
    return Response.json({ error: 'Request too large' }, { status: 413 });

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  if (
    !body ||
    typeof body !== 'object' ||
    Array.isArray(body) ||
    !('method' in body) ||
    typeof body.method !== 'string' ||
    !allowedMethods.has(body.method)
  )
    return Response.json({ error: 'RPC method not allowed' }, { status: 403 });

  try {
    const response = await fetch(upstream, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    return new Response(response.body, {
      status: response.status,
      headers: {
        'content-type': response.headers.get('content-type') ?? 'application/json',
        'cache-control': 'no-store',
      },
    });
  } catch {
    return Response.json(
      {
        jsonrpc: '2.0',
        id: 'id' in body ? body.id : null,
        error: { code: -32098, message: 'Studio RPC is temporarily unavailable' },
      },
      { status: 502 },
    );
  }
}
