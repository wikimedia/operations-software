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
Please note that Arelion will perform maintenance work as outlined below.
Planned work reference:


XXX


Action and Reason:


Change faulty card to avoid future outage

Location:


Denver


Service Window: XXX primary


Work Status: Confirmed


Service window start:


2022-11-10 10:00 UTC


Service window end:


2022-11-10 13:00 UTC


Impacted Services

XXX

Wavelength Single Link

               3 x 1 hours
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'Denver',
			start: Date.parse( '2022-11-10T10:00:00.000Z' ),
			end: Date.parse( '2022-11-10T13:00:00.000Z' )
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

test( 'sgix', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Please take note SGIX will be performing linecard replacement maintenance on Equinix SG1 SGIX switch (SW01) slot6.
This will affect the following SGIX member’s BGP session that connected to slot6 card.

Start Time: 9-Mar-2023 at 02:00 hrs (GMT+8)
End Time:  9-Mar-2023 at 06:00 hrs (GMT+8)

1. Who will be affect:
Member’s BGP sessions that connected to Equinix SG1 SGIX switch slot 6 card.
 
...
 
2. How you will be affected:
Intermittent service disruption.
Duration is approximately 4 hours.

For clarifications, please email notice@sgix.sg.
For assistance or support during the maintenance, please email noc@sgix.sg.



--------
To unsubscribe, click here:-
https://cportal.sgix.sg:8808/unsubscribe.php




--- End of automate email ---
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'SG1',
			start: Date.parse( '2023-03-08T18:00:00.000Z' ),
			end: Date.parse( '2023-03-08T22:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'de-cix', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
MAINTENANCE: Planned linecard upgrade  (OPEN)

DE-CIX Maintenance ID: DXDB:MAINT:1619

Work start: 2023-08-09 05:00 UTC
Work end: 2023-08-09 11:00 UTC

Work status: ANNOUNCED
Notification type: OPEN
Impact: Full Disruption

Affected entities:
Devices: edge01.dfw1.dfw.de-cix.net:chassis-1/5, edge01.dfw1.dfw.de-cix.net:chassis-1/6

Work description:

We will be upgrading our line cards in DFW to support more capacity. We will be migrating customers from these cards to prepare for the installation of new line cards. We expect a disruption in service during this time.

If you have any questions or concerns, please feel free to reach out to support@de-cix.net.

Affected Customers:
AS62 - CyrusOne LLC
AS10310 - Yahoo EMEA Limited
AS11492 - CABLE ONE, INC.
AS12200 - Rackspace (US, Inc./Germany GmbH)
AS13354 - zColo (previously known as CoreXchange), part of Zayo Gorup
AS13649 - Flexential Corp. / ViaWest
AS13760 - Uniti Fiber
AS15695 - Expereo International
AS33171 - Find Your Route LLC
AS36086 - Digital Realty
AS36351 - SoftLayer Technologies, Inc. (an IBM Company)
AS43531 - IX Reach LTD
AS46925 - Pavlov Media
AS47147 - ANEXIA Internetdienstleistungs GmbH
AS53828 - Network Innovations, LLC d/b/a Nitel
AS199524 - G-Core labs S.A
AS399462 - SUMOFIBER of TEXAS LLC


If you have any questions, do not hesitate to ask!

Best regards,
-- 
DE-CIX Customer Service

DE-CIX North America Inc. | 590 Madison Avenue | 21st Floor | New York | NY 10022 | Phone +1-212-796-6914 | support@de-cix.net | President Ivaylo Ivanov | https://de-cix.net/en/locations/united-states
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'edge01.dfw1.dfw.de-cix.net:chassis-1/5, edge01.dfw1.dfw.de-cix.net:chassis-1/6',
			start: Date.parse( '2023-08-09T05:00:00.000Z' ),
			end: Date.parse( '2023-08-09T11:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'digital-realty', ( assert ) => {
	const msg = new Message( 'stub' );
	/* eslint-disable no-irregular-whitespace */
	msg.textCache = `
 Summary 
Communication

Case Number
CS1183034

Case Received on
26-07-2023 10:30:13 CEST

Category
Communication

Sub category
Maintenance

Case status
Open

Dear Sir / Madam,
With reference to case CS1183034 created on 26-07-2023 10:30:13 CEST, we would like to inform you that the case has been updated as follows: Summary: Preventative maintenance on detection and automatic fire extinguishing systemSite Location : MRS2 Data Center [ Marseille, France]Impact to Service: None Expected, Customer Intervention is NOT Required Type: FireTime Start: 26 September 2023 09:00 Local timeTime End: 06 October 2023 18:00 Local time  Message: Dear Valued Customer,Digital Realty would like to inform you that a preventive maintenance of detection and automatic fire extinguishing is planned as describe above.Respectfully,Digital RealtySubject Line and Summary Section Definitions included in each notificationSubject Guide – [site] [Impact] [Notification Type] Case Reference Site Reflects the Digital Realty name of the site affected by the maintenanceImpact No Action RequiredNO customer action is required during this event.Action Required Customer action IS required during this eventAction Maybe RequiredCustomer action MAYBE required during this eventNotification TypeInformational NotificationNotification of works for information only, no intervention required ; a visual inspection of the data centre by Digital Realty personnelPreventative Maintenance NotificationNotification of routine proactive maintenance normally scheduled in advance on a regular basis – i.e. regular UPS MaintenanceCorrective Maintenance NotificationNotification of corrective maintenance following routine checks and/or proactive monitoring – i.e. a fault has been detected with a CRAC and this will require maintenance to resolve.Emergency Maintenance NotificationNotification of urgent maintenance required to prevent a service affecting fault – i.e. a hardware replacement must be performed on a CRAC to prevent temperatures from rising above agreed thresholds and interrupting service.Incident NotificationNotification of a service affecting incidentSummary Provides a brief summary of the maintenance works being scheduled or the nature of the incident.Impact to Service GuideNone Expected, Customer Intervention is NOT Required The work being undertaken is not expected to affect service to customers – i.e. a redundant Cooling Unit is being worked upon whilst the live remains operational.Potential, Customer Intervention MAY BE Required The work being undertaken may potentially affect service to customers – i.e. power work being undertaken on a UPS A-Feed, power will be provided via the B-Feed for dual fed customers. Single fed customers will need to take actionExpected, Customer Intervention WILL BE RequiredThe work being undertaken will affect service to customers – i.e. power work being undertaken on a UPS for both feeds that will certainly affect all customers connected to that UPS.    Résumé : Maintenance préventive de notre système de détection et extinction incendieEmplacement du site: MRS2 Data Center [ Marseille, France]Impact du Service: Aucun, l'intervention du client n´est pas nécessaire.Type: FeuHeure de début : 26 Septembre 2023 09:00 Heure localeHeure de fin : 06 Octobre 2023 18:00 Heure localeMessage : Madame, Monsieur,Digital Realty souhaite vous informer qu’une maintenance préventive de notre système de détection et extinction incendie est planifiée comme décrit ci-dessus.Cordialement,Digital RealtyLigne Objet et section résumé Définitions inclus dans chaque notification:Guide-sujet - [site] [impact] [Type de notification] Scénario de référenceSite Reflète le nom du site Digital Realty affecté par la maintenanceimpact Aucune action nécessaireL´intervention du client n´est pas nécessaire lors de cet événement.Action nécessaireL'action du client est nécessaire lors de cet événementAction peut être nécessaireL'action du client peut être nécessaire lors de cet événementtype de notificationNotification informativeNotification de travaux pour information, l´intervention n´est pas nécessaire, inspection visuelle du data centre par le personnel d´Digital Realty.Notification Maintenance PréventiveNotification d'une maintenance proactive de routine normalement prévue à l'avance sur une base régulière – par exemple la maintenance régulière des onduleurs.Notifications de maintenance CorrectiveNotification d'une maintenance corrective suite à des contrôles de routine et / ou une surveillance proactive - soit un défaut a été détecté avec les armoires de climatisation et une maintenance sera nécessaire pour résoudre le problème.Les notifications de maintenance d'urgenceNotification de travaux de maintenance urgents nécessaires pour empêcher un défaut de service. - Ou bien un remplacement du matériel doit être effectué sur une armoire de climatisation pour éviter que les températures augmentent au-delà des limites convenues et interrompent le service.Notification des incidentsNotification d'un incident affectant le serviceRésumé Fournit un bref résumé des travaux de maintenance prévus à l´avance, ou la nature de l'incident.Impact Guide des servicesPas d´impact, l'intervention du client n´est pas nécessaire Le travail entrepris ne devrait pas affecter le service aux clients – i.e. Travaux sur une armoire de climatisation redondante, le service reste opérationnel Potentiel, intervention du client peut être nécessaireLes travaux entrepris peuvent potentiellement affecter le service aux clients – par exemple le travail sur le courant effectué sur un onduleur A, l´alimentation sera assurée par l ´onduleur B pour les clients alimentés par deux voies. Les clients alimentés par une seule voie devront prendre les mesures. nécessaires.Attendu, l'intervention du client est nécessaireLes travaux entrepris auront une incidence sur le service aux clients - par exemple les travaux sur les onduleurs dédiés à deux voies affecteront probablement les clients connectés à cet onduleur. Please click here should you want to check the status.

Respectfully,
 Digital Realty

Contact: ecc@digitalrealty.com

Ref:MSG30954022_NrejjrAn0TpLC5OiMhP
`;
	/* eslist-enable no-irregular-whitespace */
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'MRS2 Data Center [ Marseille, France]',
			start: Date.parse( '2023-09-26T07:00:00.000Z' ),
			end: Date.parse( '2023-10-06T16:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );

test( 'GTT', ( assert ) => {
	const msg = new Message( 'stub' );
	msg.textCache = `
Planned Work Notification: Master 7570054 - New                  As part of our commitment to continually improve the quality of service we provide to our clients, we will be performing a planned work in United States, Dallas between 2023-08-08 07:00:00 - 2023-08-08 11:00:00 GMT. Please see details of the work and impact on your service below.     Detail:                  Start        2023-08-08 07:00:00 GMT                    End        2023-08-08 11:00:00 GMT                          Location        United States, Dallas                    Planned work Reason:      Maintenance on our IP platform related to Junos software upgrade                            Child Tickets        Services Affected        SLID/CCSD        CPON / Client Item Label        Service Type        Expected Impact to your Service        Site Address                              7571183        VPLS/00943500        681000-4793082        CID-2569        VPLS        90 min        1950 N Stemmons Fwy,Dallas,TX,75207,USA                       Comments (Color explanation) :            Service interruption        Service will experience interruption lasting maximum the duration value in the service row                  Resiliency Loss        Primary or backup circuit will be impacted only. Service will remain operational throughout the maintenance                  Non-Service Affecting        No Service is affected. Service will remain operational throughout the maintenance      If you have any questions regarding the planned work, please login to EtherVision or contact our Change Management Team using the email below.    Kind Regards,    GTT Network Operations        netopsadmin@gtt.net          Did you know that it is now easier than ever to log your tickets on our EtherVision portal? You will be able to answer a few troubleshooting questions and receive a ticket ID immediately. Check out this quick tutorial here. EtherVision also helps you check on status of existing tickets and access your escalation list.  If you do not have an EtherVision login, you can contact your company’s account administrator or submit a request on our website.
`;
	assert.propContains( msg.work, {
		0: {
			allday: false,
			details: 'United States, Dallas',
			start: Date.parse( '2023-08-08T07:00:00.000Z' ),
			end: Date.parse( '2023-08-08T11:00:00.000Z' )
		}
	} );
	assert.strictEqual( msg.work.length, 1 );
} );
