// Run with: node scripts/record_demo.mjs
// Windows: requires installed frontend dependencies, .venv, Playwright Chromium, and ffmpeg.
// All intermediate files, including the fresh SQLite database, are retained in a unique temp directory.
import { spawn, spawnSync } from 'node:child_process'
import { createRequire } from 'node:module'
import { mkdtemp, copyFile, mkdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import net from 'node:net'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const frontend = path.join(root, 'frontend')
const requireFrontend = createRequire(path.join(frontend, 'package.json'))
const { chromium, expect } = requireFrontend('@playwright/test')
const { createServer } = await import(pathToFileURL(requireFrontend.resolve('vite')).href)
const apiPort = 18172, webPort = 15172
if (process.platform !== 'win32') throw new Error('Port ownership and process cleanup currently require Windows')
const work = await mkdtemp(path.join(tmpdir(), 'hpm-demo-'))
const db = path.join(work, 'synthetic.sqlite').replaceAll('\\', '/')
console.log(`Isolated files: ${work}`)

async function checkFree(port) {
  await new Promise((resolve, reject) => {
    const socket = net.createServer()
    socket.once('error', reject)
    socket.listen(port, '127.0.0.1', () => socket.close(resolve))
  })
}
await checkFree(apiPort)
await checkFree(webPort)

let api, vite, browser, context
try {
  const python = process.platform === 'win32' ? path.join(root, '.venv', 'Scripts', 'python.exe') : path.join(root, '.venv', 'bin', 'python')
  api = spawn(python, ['-B', '-m', 'hpm'], {
    // Alembic resolves its script directory relative to the repository root.
    cwd: root,
    env: { ...process.env, PYTHONPATH: path.join(root, 'src'), PYTHONDONTWRITEBYTECODE: '1',
      APP_ENV: 'demo', DATABASE_URL: `sqlite:///${db}`, HPM_RESET_DB: '0', SEED_ON_STARTUP: 'false',
      HOST: '127.0.0.1', PORT: String(apiPort), ALLOW_NETWORK_BIND: 'false', CORS_ORIGINS: `http://127.0.0.1:${webPort}` },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  let logs = ''
  const collect = chunk => { logs += chunk.toString(); process.stdout.write(chunk) }
  api.stdout.on('data', collect); api.stderr.on('data', collect)
  await new Promise((resolve, reject) => {
    const deadline = Date.now() + 90000
    const poll = async () => {
      if (api.exitCode !== null) return reject(new Error(`API exited: ${api.exitCode}\n${logs}`))
      if (Date.now() > deadline) return reject(new Error(`API startup timed out\n${logs}`))
      // Alembic can disable Uvicorn's startup logger. Verify the listening PID against
      // the PID reported by our child before contacting the endpoint.
      const pid = logs.match(/Started server process \[(\d+)\]/)?.[1]
      if (pid) {
        const ports = spawnSync('netstat', ['-ano', '-p', 'tcp'], { encoding: 'utf8' }).stdout ?? ''
        const owned = ports.split(/\r?\n/).some(line => {
          const parts = line.trim().split(/\s+/)
          return parts[1] === `127.0.0.1:${apiPort}` && parts[3] === 'LISTENING' && parts[4] === pid
        })
        if (owned) {
          try { if ((await fetch(`http://127.0.0.1:${apiPort}/ready`)).ok) return resolve() } catch {}
        }
      }
      setTimeout(poll, 500)
    }
    api.once('error', reject); poll()
  })
  vite = await createServer({
    root: frontend, configFile: path.join(frontend, 'vite.config.ts'), configLoader: 'runner', cacheDir: path.join(work, 'vite-cache'),
    server: { host: '127.0.0.1', port: webPort, strictPort: true,
      proxy: Object.fromEntries(['/api', '/health', '/ready'].map(key => [key, `http://127.0.0.1:${apiPort}`])) },
  })
  await vite.listen()
  browser = await chromium.launch({ headless: true })
  context = await browser.newContext({ viewport: { width: 1100, height: 720 }, deviceScaleFactor: 1,
    recordVideo: { dir: work, size: { width: 1100, height: 720 } } })
  const page = await context.newPage()
  const pause = ms => page.waitForTimeout(ms)
  await page.goto(`http://127.0.0.1:${webPort}/import`)
  await expect(page.getByRole('button', { name: /Generate synthetic log/ })).toBeVisible()
  await pause(1500)
  await page.getByRole('button', { name: /Generate synthetic log/ }).click()
  await expect(page.getByTestId('mapping-case_id')).toHaveValue('case_id', { timeout: 60000 })
  await expect(page.getByTestId('timezone')).toHaveValue('Europe/Berlin')
  await page.getByText('Field mapping', { exact: true }).scrollIntoViewIfNeeded()
  await pause(1500)
  await page.getByRole('button', { name: 'Import dataset' }).click()
  const quality = page.getByTestId('quality-panel')
  await expect(quality).toBeVisible({ timeout: 60000 })
  await expect(quality.getByTestId('quality-cases')).not.toHaveText('0')
  await quality.scrollIntoViewIfNeeded()
  await pause(1800)
  await page.getByRole('link', { name: 'Open process map' }).click()
  await expect(page.getByTestId('node-Interview Scheduled')).toBeVisible({ timeout: 60000 })
  await pause(2200)
  const before = await page.getByTestId('visible-edges').innerText()
  await page.getByTestId('edge-slider').fill('50')
  await expect(page.getByTestId('visible-edges')).not.toHaveText(before)
  await pause(1500)
  await page.getByTestId('node-Interview Scheduled').click()
  await expect(page.getByTestId('details-drawer')).toContainText('Cases')
  await pause(2000)
  await page.goto(`http://127.0.0.1:${webPort}/bottlenecks`)
  const card = page.getByTestId('insight-card').first()
  await expect(card).toContainText('Interview Scheduled', { timeout: 60000 })
  await expect(card).toContainText('Sample size')
  await pause(2500)
  const video = page.video()
  await context.close(); context = undefined
  const videoPath = await video.path()
  console.log(`Recorded browser video: ${videoPath}`)
  const gif = path.join(work, 'demo.gif')
  const result = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-n', '-i', videoPath,
    '-filter_complex', 'fps=6,scale=1000:-2:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff:max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle',
    '-loop', '0', gif], { stdio: 'inherit' })
  if (result.status !== 0) throw new Error(`ffmpeg failed: ${result.error ?? result.status}`)
  await mkdir(path.join(root, 'docs', 'assets'), { recursive: true })
  await copyFile(gif, path.join(root, 'docs', 'assets', 'demo.gif'))
  console.log('Verified synthetic import, quality, map filter, node details and bottleneck; GIF written to docs/assets/demo.gif')
} finally {
  if (context) await context.close()
  if (browser) await browser.close()
  if (vite) await vite.close()
  // The Windows venv launcher spawns the real interpreter; stop only this process tree.
  if (api && api.exitCode === null) spawnSync('taskkill', ['/PID', String(api.pid), '/T', '/F'], { stdio: 'ignore' })
}
