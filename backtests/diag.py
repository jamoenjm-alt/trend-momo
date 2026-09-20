# -*- coding: utf-8 -*-
import io
s=io.open('regime-board.html',encoding='utf-8').read()
i=s.find('const HORIZONS')
j=s.find('];', i)+2
block=s[i:j]
print('--- FILE HORIZONS block repr (first 400) ---')
print(repr(block[:400]))
print('--- total block len ---', len(block))
# my intended old string, literal — via doubled backslash in THIS source:
old=("const HORIZONS = [\n"
"  { k:'w1', label:'1 Week',   hold:'~5 trading days', avg:'+0.3%',  win:'59%', spy:'+0.4%',  tone:'flat',   note:'No reliable edge this short \\u2014 near coin-flip. Momentum needs weeks.' },")
fs=block[:len(old)]
print('--- match head?', fs==old)
for k,(a,b) in enumerate(zip(old,fs)):
    if a!=b:
        print('DIFF at',k,'old=',repr(old[k-12:k+6]),'file=',repr(fs[k-12:k+6]));break
else:
    print('head identical for',len(old),'chars')
