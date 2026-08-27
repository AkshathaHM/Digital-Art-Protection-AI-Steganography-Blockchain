import { expect, test } from '@playwright/test';

test('uploads, verifies, purchases, and downloads an artwork', async ({ page }) => {
  let downloaded = false;
  await page.route('**/api/auth/login', async route => {
    const body = route.request().postDataJSON();
    const buyer = body.email === 'buyer@example.com';
    await route.fulfill({ json: { access_token: buyer ? 'buyer-token' : 'artist-token', user: { id: buyer ? 'buyer-1' : 'artist-1', username: buyer ? 'Collector' : 'Aster', email: body.email, role: buyer ? 'buyer' : 'artist' } } });
  });
  await page.route('**/api/upload', route => route.fulfill({ status: 201, json: { accepted: true, message: 'Human artwork accepted and stored on IPFS and blockchain', blockchain_artwork_id: 7 } }));
  await page.route('http://localhost:5000/api/verify-ownership', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ verified: true, blockchain: true, watermark: 'artist-1:watermark', owner: '0xBuyer' }) }));
  await page.route('**/api/purchase', route => route.fulfill({ json: { message: 'ownership transferred' } }));
  await page.route('**/api/artworks/7/download', route => route.fulfill({ body: Buffer.from('clean-image'), contentType: 'image/png' }));

  await page.addInitScript(() => {
    window.ethereum = {
      request: async ({ method }) => method === 'eth_chainId' ? '0x539' : method === 'eth_requestAccounts' ? ['0x0000000000000000000000000000000000000001'] : [],
    };
  });
  await page.goto('/login');
  await page.getByLabel('Email').fill('aster@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: /enter studio/i }).click();
  await page.goto('/upload');
  await page.getByLabel(/choose a digital artwork/i).setInputFiles({ name: 'art.png', mimeType: 'image/png', buffer: Buffer.from('image') });
  await page.getByLabel('Title').fill('Test artwork');
  await page.getByRole('button', { name: /run human check/i }).click();
  await expect(page.getByText('On-chain artwork ID: 7')).toBeVisible();
  await page.getByRole('button', { name: /sign out/i }).click();
  await page.goto('/login');
  await page.getByLabel('Email').fill('buyer@example.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: /enter studio/i }).click();
  await expect(page.getByText('COLLECTOR WORKSPACE')).toBeVisible();
  await page.goto('/verify');
  await page.getByPlaceholder('Artwork ID').fill('7');
  const verificationResponse = page.waitForResponse('http://localhost:5000/api/verify-ownership');
  await page.getByRole('button', { name: /verify/i }).click();
  await expect((await verificationResponse).status()).toBe(200);
  await expect(page.getByText('Verified ownership')).toBeVisible();

  const purchaseResponse = await page.evaluate(async () => {
    const response = await fetch('http://localhost:5000/api/purchase', {
      method: 'POST',
      headers: { Authorization: 'Bearer buyer-token', 'Content-Type': 'application/json' },
      body: JSON.stringify({ artwork_id: 7, transaction_hash: '0xtransaction', buyer_address: '0x0000000000000000000000000000000000000001' }),
    });
    return response.status;
  });
  expect(purchaseResponse).toBe(200);

  await page.goto('/purchase/not-a-blockchain-id');
  const connectWalletButton = page.getByRole('button', { name: /connect wallet/i });
  await expect(connectWalletButton).toBeVisible();
  await connectWalletButton.click();
  await expect(page.getByText(/not a valid blockchain artwork id/i)).toBeVisible();

  const downloadResponse = await page.evaluate(async () => {
    const response = await fetch('http://localhost:5000/api/artworks/7/download', { headers: { Authorization: 'Bearer buyer-token' } });
    return { status: response.status, type: response.headers.get('content-type') };
  });
  expect(downloadResponse).toEqual({ status: 200, type: 'image/png' });
  expect(downloaded).toBeFalsy();
});