import json,sys,time
from pathlib import Path
from threading import Event
from tests.factories.first_eligibility import first_eligibility_scenario
from tests.integration.test_collection import shell,sql,command,wait_for

class MessageBarrier(Event):
    def wait(self, timeout=None):
        return super().wait(120)

private=Path(sys.argv[1]);private.mkdir(parents=True,exist_ok=True)
with first_eligibility_scenario(private,sample_ready=False) as (instance,source,clock,channel):
    with instance.private_file.open('a') as env:
        env.write('GARIMPEI_ALERT_TIMEOUT=40\n')
    command(instance,'./scripts/stop.sh');command(instance,'./scripts/init.sh','--disposable')
    def state(action):
        records=sql(instance,"SELECT state,reason,body,confirmed_message FROM runtime_alertintent ORDER BY created_at")
        control=sql(instance,"SELECT requested_enabled,revision FROM runtime_robotcontrol")
        print(json.dumps({'action':action,'url':f'http://127.0.0.1:{instance.config.web_port}','posts':len([c for c in channel.calls if c[0]=='POST']),'messages':len(channel.messages),'control':control,'intents':[list(r) for r in records],'source_calls':len(source.calls)},default=str),flush=True)
    state('ready')
    for raw in sys.stdin:
        action=raw.strip()
        if action=='arm':
            channel.hold_post=True;channel.release=MessageBarrier();channel.held.clear()
            source.rows['16006']['description']='Funciona perfeitamente.'
            source.rows['16001']['description']='Usado. Funciona perfeitamente.'
            clock.advance(61)
            wait_for(channel.held.is_set,'authorized WAHA POST at real server barrier',seconds=55)
            state(action)
        elif action=='release':
            channel.release.set();channel.hold_post=False;clock.advance(61)
            wait_for(lambda:sql(instance,"SELECT count(*) FROM runtime_alertintent WHERE state='confirmed'")==[(1,)],'authorized message receipt',seconds=25)
            state(action)
        elif action=='restart':
            before=len([c for c in channel.calls if c[0]=='POST'])
            command(instance,'./scripts/stop.sh');command(instance,'./scripts/init.sh','--disposable')
            assert sql(instance,'SELECT requested_enabled FROM runtime_robotcontrol')==[(False,)]
            assert len([c for c in channel.calls if c[0]=='POST'])==before
            state(action)
        elif action=='prepare-resume':
            source.rows['16001']['price']='R$ 900,00';clock.advance(61)
            state(action)
        elif action=='wait-resume':
            wait_for(lambda:len([c for c in channel.calls if c[0]=='POST'])==2,'exactly one resumed price reduction',seconds=55)
            wait_for(lambda:sql(instance,"SELECT count(*) FROM runtime_alertintent WHERE state='confirmed'")==[(2,)],'reduction receipt',seconds=25)
            state(action)
        elif action=='inspect':state(action)
        elif action=='exit':break
        else:raise RuntimeError('Unknown action '+action)
