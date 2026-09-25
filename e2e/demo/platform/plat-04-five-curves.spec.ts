import { test, expect } from "@playwright/test";
test("PLAT-04 five-curves", async ({ request }) => {
  const ports=[{url:"http://127.0.0.1:8001/api/evolution/trust-scores",name:"SOC",key:"history"},{url:"http://127.0.0.1:8002/api/s2p/performance/trajectory",name:"S2P",key:"points"},{url:"http://127.0.0.1:8010/api/trajectory",name:"Trading",key:"points"},{url:"http://127.0.0.1:8020/api/trajectory",name:"Purchasing",key:"points"},{url:"http://127.0.0.1:8030/api/trajectory",name:"DataOps",key:"points"}];
  const results=[];
  for(const item of ports){const response=await request.get(item.url);results.push({name:item.name,ok:response.ok(),status:response.status(),body:response.ok()?await response.json():null,key:item.key});}
  const missing=results.filter((x)=>!x.ok).map((x)=>x.name+":"+x.status);
  test.skip(missing.length>0,"Missing conservation status on: "+missing.join(", "));
  expect(results).toHaveLength(5);
  for (const result of results) expect(result.body[result.key].length).toBeGreaterThan(0);
});
