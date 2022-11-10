/* eslint-disable no-tabs */
'use strict';

const Message = require( '../ops-maint-gcal.js' );
const { test } = QUnit;

test( 'No parser found', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = 'unparseable text';
	assert.strictEqual( msg.work, null );
} );

test( 'Telia single work', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Please note that Telia Carrier will perform maintenance work as outlined below.
Planned work reference:	...
Action and Reason:	...
Location:	Scottsville/VA, US

Service Window: PWICID primary	Work Status: Confirmed
Service window start:	2021-08-31 04:00 UTC
Service window end:	2021-08-31 12:00 UTC
Impacted Services
IC-ID	Wavelength Single Link	1 x 6 hours
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Scottsville/VA, US',
			start: Date.parse( '2021-08-31T04:00:00.000Z' ),
			end: Date.parse( '2021-08-31T12:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'Lumen', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Scheduled Maintenance #: 1234

Summary:

What?
Lumen intends to carry out internal maintenance within its network.

Why?
Work is required

Where?
Chippenham, United Kingdom

When?
See Customer Impact table below

Lumen would like to apologise for any inconvenience caused by this maintenance.

Updates:


2022-11-09 11:07:15 GMT - This maintenance is scheduled.


Customer Impact:

25330216-1 StartEnd2022-12-02 21:00 GMT (Greenwich Mean Time)2022-12-03 05:00 GMT (Greenwich Mean Time)Maintenance Location(s): Dauntsey United Kingdom; Brinkworth United KingdomCustomer NameCircuit IDAlt Circuit IDBandwidthA LocationZ LocationImpact TypeMaximum DurationOrder NumberXXXOutage8 hours

Click here for assistance on this scheduled maintenance via Email.

Click here for immediate information on scheduled maintenances via the Lumen Customer Portal.

Click here to manage your notification subscriptions via the Lumen Portal.
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Dauntsey United Kingdom; Brinkworth United Kingdom',
			start: Date.parse( '2022-12-02T21:00:00.000Z' ),
			end: Date.parse( '2022-12-03T05:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'NTT', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Event Details

Ticket Number:
	GIN-ID

Start Date/Time:
	2021-09-01 07:00 UTC

End Date/Time:
	2021-09-01 10:00 UTC

Direct Impact:
	Users connected to this device will experience downtime during this maintenance window.


Reason:
	We will be performing an urgent hardware maintenance affecting the service(s) listed below.

Affected Services

Service ID	Service Type	IP Address	IPv6 Address	Device	Port ID	Market	Impact Level
stub description

Contact Information

NTT Global IP Network (AS2914)
Network Operations Center
Dallas, Texas, USA

	Email:noc@ntt.net
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'stub description',
			start: Date.parse( '2021-09-01T07:00:00.000Z' ),
			end: Date.parse( '2021-09-01T10:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'Equinix single work single day', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Dear Equinix Customer,

DATE: 12-SEP-2021

SPAN: 12-SEP-2021 - 12-SEP-2021

LOCAL: SUNDAY, 12 SEP 01:00 - SUNDAY, 12 SEP 05:00
UTC: SATURDAY, 11 SEP 17:00 - SATURDAY, 11 SEP 21:00

IBX(s): SG1,SG2,SG3,SG4,SG5

DESCRIPTION:Please be advised that one of our upstream providers will be performing a software upgrade

There will be no impact to your services as traffic will be automatically rerouted to our alternate provider.
`;
	assert.propContains( msg.work, {
		0: {
			allday: true,
			details: 'SG1,SG2,SG3,SG4,SG5',
			start: Date.parse( '2021-09-12T00:00:00.000Z' ),
			end: Date.parse( '2021-09-12T00:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );

	const link = msg.work[ 0 ].gcalendarLink( 'calendar_id', 'link text' );
	assert.strictEqual( new URL( link ).searchParams.get( 'dates' ), '20210912/20210913' );
} );

test( 'Equinix multiple work multiple days', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Dear Equinix Customer,

DATE: 02-SEP-2021 - 06-SEP-2021

SPAN: 02-SEP-2021 - 06-SEP-2021

LOCAL: THURSDAY, 02 SEP 14:00 - FRIDAY, 03 SEP 06:00
UTC: THURSDAY, 02 SEP 19:00 - FRIDAY, 03 SEP 11:00

LOCAL: FRIDAY, 03 SEP 14:00 - SATURDAY, 04 SEP 06:00
UTC: FRIDAY, 03 SEP 19:00 - SATURDAY, 04 SEP 11:00

LOCAL: SATURDAY, 04 SEP 14:00 - SUNDAY, 05 SEP 06:00
UTC: SATURDAY, 04 SEP 19:00 - SUNDAY, 05 SEP 11:00

LOCAL: SUNDAY, 05 SEP 14:00 - MONDAY, 06 SEP 06:00
UTC: SUNDAY, 05 SEP 19:00 - MONDAY, 06 SEP 11:00

IBX: CH2

DESCRIPTION: Equinix engineering staff along with the UPS vendor will be performing corrective repairs on

The equipment being maintained supports your circuits indicated in the table.
`;
	assert.propContains( msg.work, {
		0: {
			allday: true,
			details: 'CH2',
			start: Date.parse( '2021-09-02T00:00:00.000Z' ),
			end: Date.parse( '2021-09-06T00:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );

	const link = msg.work[ 0 ].gcalendarLink( 'calendar_id', 'link text' );
	assert.strictEqual( new URL( link ).searchParams.get( 'dates' ), '20210902/20210906' );
} );

test( 'euNetworks single', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Maintenance Announcement

Dear Customer,

Please be advised that euNetworks will perform an urgently required hardware replacement on the dates and times shown below.
This is an emergency. Every delay of these works could have a critical impact on our network and therefore on your service stability.
Should you have any questions please contact our Change Management Team by replying to this e-mail.

Best Regards,
Your euNetworks Change Management Team

Sehr geehrter Kunde,
mit diesem Schreiben möchten wir Sie über einen dringend notwendigen Hardwaretausch im Netz der euNetworks informieren.
Dies ist eine Notfall-Situation. Jede Verzögerung der Arbeiten könnte die Funktionalität unseres Netzes und damit die Stabilität Ihres Services gefährden.
Bei Fragen antworten Sie bitte auf diese E-Mail. Unser Change Management Team ist Ihnen gerne behilflich.

Mit freundlichen Grüßen
Ihr euNetworks Change Management Team

Ticket Number: 666

Service Affecting: Yes
Impact: 2 Hours Outage

Reason for Request: Hardware Defect

Location Description: Road

Start Time: 2022-05-06 22:01 GMT
End Time: 2022-05-07 03:00 GMT

Service:
Number, ID, Name	Location A
Location Z	Work
Status
S0000000, null,
A: aaa
Z: zzz



ref:00000:ref
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Road',
			start: Date.parse( '2022-05-06T22:01:00.000Z' ),
			end: Date.parse( '2022-05-07T03:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'euNetworks update', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Maintenance Announcement

UPDATE #8: Ticket 00000 has been updated. Updated values are marked bold.

Dear Customer,

Please be advised that euNetworks will perform a necessary cable relocation on the dates and times shown below.

Should you have any further questions regarding these works please contact our Change Management Team by replying to this e-mail.

Best Regards,

euNetworks Change Management Team

Sehr geehrter Kunde,

mit diesem Schreiben möchten wir Sie über einen notwendigen Kabel-Umzug im Netz der euNetworks informieren.

Für weitere Fragen bezüglich dieser Arbeiten antworten Sie bitte auf diese Email. Unser Change Management Team ist Ihnen gerne behilflich.

Mit freundlichen Grüßen

euNetworks Change Management Team

Ticket Number: 00000

Service Affecting: Yes
Impact: 8 Hours Outage

Reason for Request: Road Works

Additional Customer Information: Info

Location Description: Road

Start Time: 2022-05-09 20:00 GMT
End Time: 2022-05-10 04:00 GMT

Start Time (OLD): 2022-05-03 20:00 GMT
End Time (OLD): 2022-05-04 04:00 GMT


Service:
Number, ID, Name Location A
Location Z Work
Status
S0000, null,
A: XXX
Z: XXX

ref:0000:ref
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Road',
			start: Date.parse( '2022-05-09T20:00:00.000Z' ),
			end: Date.parse( '2022-05-10T04:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'orange', ( assert ) => {
	const msg = new Message( 'stub' );
	// Note: the text trailing/leading spaces are significant here.
	msg.textCache = `
      This is an automatically generated message, please do not reply. To reply, kindly click on the following e-mail address: csciw@orange.com
    
      Friday 29/Apr/2022 08:07 (UTC)
    
            You 
            WIKIMEDIA FOUNDATION, INC. 
             
            To 
             
       NOC 
    
      noc@wikimedia.org 
    
            Us
CSCIW
CSCIW , F.O. Reception
Phone:
Fax:
Email: csciw@orange.com
    
      Service impacting change N° T00000 impacting Orange's network
    
 
Hello,
 
       As part of improving the quality of our infrastructures, we need to work on our network soon.
 
 
Characteristics of the operation 
    
      Type: Service impacting change 
    
      Nature: Orange intervention 
    
      Cause: Software upgrade 
    
      Beginning: Thursday 12/May/2022 at 22:00 (UTC) 
    
      End: Friday 13/May/2022 at 01:00 (UTC) 
    
      Duration: 3h 
    
      Impact: Complete failure 
    
      Number of impacted services: 1 
    
 
 
The services concerned by the operation are listed in the table hereafter. 
 
    
    Thanks for your faithful.
    
    
      Your Orange customer service
    
 
  Table with the critical product
 
          No critical product identified
  
   Table with the other product
  
      Product type
    
    
      Product ID
    
    
      Ends
    
    
      Sites
    
    
      Corporate name
    
     
      Service set
    
    
      Role
    
  
    
      All routes 
    
    
      XXX
    
       - - - - - -  
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Complete failure',
			start: Date.parse( '2022-05-12T22:00:00.000Z' ),
			end: Date.parse( '2022-05-13T01:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'Telxius', ( assert ) => {
	const msg = new Message( 'stub' );
	// Note: the text trailing/leading spaces are significant here.
	msg.textCache = `
Dear Sirs // Estimados Señores,
WIKIMEDIA FOUNDATION, INC.
Please find below our Scheduled Work Notification // Abajo encontrará nuestra Notificación de Trabajo Programado:
NOTIFICATION NUMBER // NUMERO DE NOTIFICACION: XXX
NOTIFICATION TYPE // TIPO DE NOTIFICACION: Normal
DESCRIPTION // DESCRIPCION: A scheduled work will be carried out to relocate fiber cable due to civil works. // Se realizará un trabajo programado para reubicar cable de fibra debido a obras civiles.
SERVICE IMPACT // IMPACTO EN SERVICIOS: SWITCH HITS
LOCATION // LOCALIDAD: Paris, France
SCHEDULE // VENTANA(S) DE TRABAJO (UTC):
07-Dec-2022 21:00 - 08-Dec-2022 05:00
AFFECTED CIRCUITS // CIRCUITOS AFECTADOS:

[English]
If you shall experience any problem with your services due to the performing of this task, please contact our Capacity Services NOC at +511 411 0070 or mailing to customerservice.capacity@telxius.com.
We would like to apologize for any inconvenience caused by this maintenance to you and your customers. If any additional question appears, do not hesitate to contact us.
Our personnel will be permanently available for you.
[Español]
Si experimenta algún problema con su servicio debido a la realización de esta actividad programada, por favor comuníquese a nuestro NOC de Capacity Services vía el +511 411 0070 o al correo customerservice.capacity@telxius.com.
Lamentamos los inconvenientes que este mantenimiento pueda causarle a usted o sus clientes. Si una nueva consulta surgiera, no dude en comunicarse con nosotros, nuestro personal estará permanentemente disponible para usted.

Este mensaje y sus adjuntos se dirigen exclusivamente a su destinatario, puede contener información privilegiada o confidencial y es para uso exclusivo de la persona o entidad de destino. Si no es usted. el destinatario indicado, queda notificado de que la
 lectura, utilización, divulgación y/o copia sin autorización puede estar prohibida en virtud de la legislación vigente. Si ha recibido este mensaje por error, le rogamos que nos lo comunique inmediatamente por esta misma vía y proceda a su destrucción.

The information contained in this transmission is confidential and privileged information intended only for the use of the individual or entity named above. If the reader of this message is not the intended recipient, you are hereby notified that any dissemination,
 distribution or copying of this communication is strictly prohibited. If you have received this transmission in error, do not read it. Please immediately reply to the sender that you have received this communication in error and then delete it.

Esta mensagem e seus anexos se dirigem exclusivamente ao seu destinatário, pode conter informação privilegiada ou confidencial e é para uso exclusivo da pessoa ou entidade de destino. Se não é vossa senhoria o destinatário indicado, fica notificado de que a
 leitura, utilização, divulgação e/ou cópia sem autorização pode estar proibida em virtude da legislação vigente. Se recebeu esta mensagem por erro, rogamos-lhe que nos o comunique imediatamente por esta mesma via e proceda a sua destruição
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Paris, France',
			start: Date.parse( '2022-12-07T21:00:00.000Z' ),
			end: Date.parse( '2022-12-08T05:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );
