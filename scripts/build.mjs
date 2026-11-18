import * as esbuild from 'esbuild';
import { cp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
await rm('dist',{recursive:true,force:true});
await mkdir('dist',{recursive:true});
await cp('web/public','dist',{recursive:true});
const html=(await readFile('web/index.html','utf8')).replace('<script type="module" src="/main.js"></script>','<link rel="stylesheet" href="./assets/main.css"><script type="module" src="./assets/main.js"></script>');
await writeFile('dist/index.html',html);
const options={entryPoints:['web/main.js'],bundle:true,format:'esm',minify:true,outdir:'dist/assets',define:{'import.meta.env.BASE_URL':'"./"'},logLevel:'info'};
if(process.argv.includes('--serve')){const context=await esbuild.context(options);await context.watch();await context.serve({servedir:'dist',host:'127.0.0.1',port:5173});console.log('Local: http://127.0.0.1:5173');}else await esbuild.build(options);
