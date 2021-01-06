#!/usr/bin/env python3

from colors import css_colors
from functools import wraps
from snips_skill import *
import json, random, time


_, ngettext = get_translations( __file__)


def require_capability( capability, response=_("That's impossible")):
    'Decorator to ensure a device capability'
    def wrapper( method):
        @wraps( method)
        def wrapped( client, userdata, msg):
            client.capability( msg.payload, capability, response)
            return method( client, userdata, msg)
        return wrapped
    return wrapper


def confirm( *args):
    return random.choice( 2 * args + CONFIRMATIONS)


class LightsSkill( MultiRoomConfig, Skill):
    
    'Control lights and switches via zigbee2mqtt'
    
    LOCATION_SLOT = 'location'
    
    SETTINGS = {} # Stores device state, keyed by device name
    
    
    @topic( 'zigbee/+', payload_converter=json.loads)
    def status( self, userdata, msg):
        'Collect zigbee2mqtt device status reports'
        self.log.debug( 'Payload: %s', msg.payload)
        device = msg.topic.split('/')[1]
        self.SETTINGS[ device] = msg.payload


    def get_status( self, payload, key):
        conf = self.get_room_config( payload)
        device = conf.get( 'device')
        if device:
            settings = self.SETTINGS.get( device)
            if settings is not None:
                return settings.get( key)
        

    def capability( self, payload, capability, response=_("That's impossible")):
        'Check against the config that a given device can handle the requested action'
        caps = self.get_room_config( payload).get( 'capabilities', '')
        if capability not in map( lambda s: s.strip(), caps.split( ',')):
            raise SnipsError( response)


    def switch( self, msg, args, response=_('done')):
        ''' Manipulate a device through zigbee2mqtt.
            If a confirmation is requested in the device config,
            send an audible reply.
        '''
        if self.all_rooms( msg.payload):
            for conf in self.configuration.values():
                device = conf.get( 'device')
                if device: self._switch( device, args)
            return response
        
        self._switch( self._get_device( msg.payload), args)
        if not self.in_current_room( msg.payload):
            return response


    def _get_device( self, payload, msg=_('unknown device')):
        conf = self.get_room_config( payload)
        device = conf.get( 'device')
        if device is None: raise SnipsError( msg)
        return device
        
    
    def _switch( self, device, args):
        base_topic = self.get_config().get( 'base_topic', 'zigbee2mqtt')
        topic = '%s/%s/set' % (base_topic, device)
        self.publish( topic, json.dumps( args))

        
    @intent( 'domi:LampenAusSchalten', silent=True)
    @min_confidence( 0.6)
    def switch_off( self, userdata, msg):
        if self.get_status( msg.payload, 'state') == 'OFF':
            return _('It is already off')
        return self.switch( msg, { 'state' : 'OFF' },
            confirm( _('switched off')))
    

    @intent( 'domi:LampenAnSchalten', silent=True)
    @min_confidence( 0.6)
    def switch_on( self, userdata, msg):
        args = { 'state' : 'ON' }
        if 'brightness' in msg.payload.slots:
            percent = msg.payload.slot_values['brightness'].value
            if percent < 5:
                return self.switch_off( userdata, msg)
            if percent <= 95:
                self.capability( msg.payload, 'brightness',
                    _('This device can be only switched on or off.'))
            args[ 'brightness'] = 254 * percent / 100
        elif self.get_status( msg.payload, 'state') == 'ON':
            return _('It is already on')

        return self.switch( msg, args, confirm( _('switched on')))


    @intent( 'domi:FarbeWechseln', silent=True)
    @min_confidence( 0.6)
    @require_capability( 'color')
    @require_slot( 'color', prompt=_('which color?'))
    def change_color( self, userdata, msg):
        css_name = msg.payload.slot_values['color'].value
        if css_name not in css_colors:
            raise SnipClarificationError( _('which color?'), 
                payload.intent.intent_name, 'color')
            
        r, g, b = css_colors[ css_name]
        return self.switch( msg, { 'state' : 'ON',
            'color' : { 'r': r, 'g': g, 'b': b }})


    @intent( 'domi:LichtDimmen', silent=True)
    @min_confidence( 0.7)
    @require_capability( 'brightness',
            _('This device can be only switched on or off.'))
    @require_slot( 'action', prompt=_('brighter or lower?'))
    def dim_light( self, userdata, msg):

        brightness = self.get_status( msg.payload, 'brightness')
        if brightness is None:
            return _("That's currently not possible")
        
        action = msg.payload.slot_values['action'].value
        conf = self.get_room_config( msg.payload)
        offset = conf.getint( 'dim_step', 50)
        if action != 'higher': offset = -offset
        brightness = max( min( 254, brightness + offset), 0)
        
        is_on = self.get_status( msg.payload, 'state')
        if is_on != 'ON' and offset > 0:
            return self.switch( msg,
                { 'state' : 'ON', 'brightness' : offset })
        
        if brightness <= 0:
            return self.switch( msg, { 'state' : 'OFF' })

        return self.switch( msg, { 'brightness' : brightness })
        

    @intent( 'domi:SzenenSchalten')
    def not_implemented( self, userdata, msg):
        return _('Not yet implemented')


# Let's go!
if __name__ == '__main__': LightsSkill().run()
