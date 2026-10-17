async (page) => {
  await page.setViewportSize({ width: 1300, height: 1350 });
  await page.evaluate(() => window.ready);
  const base = "assets/2d/T-024-人物三视图/composite-v1/";
  const names = ["grey","ambrose","constance","iris","gideon","latente"];
  for (let i=0;i<names.length;i++) {
    await page.evaluate(i => window.setPortrait(i), i);
    await page.locator("#frame").screenshot({path: base+"aligned/"+names[i]+".png", animations:"disabled"});
  }
  for (const t of [0,3,6,8,10,12]) {
    await page.evaluate(t => window.setFrame(t), t);
    await page.locator("#frame").screenshot({path: base+"review/frame-"+t.toString().padStart(2,"0")+".png", animations:"disabled"});
  }
  await page.evaluate(() => window.setFrame(12));
  await page.locator("#frame").screenshot({path: base+"final/composite.png", animations:"disabled"});
  const pendingDownload=page.waitForEvent("download",{timeout:30000});
  const recording=page.evaluate(()=>window.recordPreview());
  const download=await pendingDownload;
  await download.saveAs(base+"review/composite-preview-v1.webm");
  await recording;
  return {alignedPortraits:6,keyframes:6,finalFrame:true,videoSaved:true};
}
